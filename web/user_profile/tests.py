from datetime import datetime, timedelta
from unittest.mock import patch

import django.utils.timezone
import pytz
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APIRequestFactory

import hera.thirdparties
from hera.settings import HERA_OTP_LENGTH
from user_profile.models import OnboardingProgress, PhoneNumberChangeRequest, UserProfile
from user_profile.throttles import ChangePhoneNumberRequestThrottle


class UserProfileViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create(
            username="+6590000000",
        )
        _ = Token.objects.create(
            user=user
        )

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = User.objects.get(username__exact="+6590000000")
        self.token = Token.objects.get(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_user_profile_should_return_empty(self):
        response = self.client.get('/user_profiles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_list_user_profile_should_return_existing_profile(self):
        _ = UserProfile.objects.create(
            user=self.user,
            name="Ms Red",
            gender="FEMALE",
            date_of_birth="1999-01-01",
            agree_to_terms_at="2021-01-01T00:00Z",
        )
        response = self.client.get('/user_profiles/')
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], "Ms Red")

    def test_get_user_profile_should_return_correct_data(self):
        _ = UserProfile.objects.create(
            user=self.user,
            name="Ms Red",
            gender="FEMALE",
            date_of_birth="1999-01-01",
            agree_to_terms_at="2021-01-01T00:00Z",
        )
        response = self.client.get(f'/user_profiles/{self.user.id}/')
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["name"], "Ms Red")
        self.assertEqual(response_data["gender"], "FEMALE")
        self.assertEqual(response_data["date_of_birth"], "1999-01-01")
        self.assertEqual(response_data["agree_to_terms_at"], "2021-01-01T00:00:00Z")

    def test_post_user_profile_should_succeed(self):
        response = self.client.post('/user_profiles/', {
            'name': 'Mr Green',
            'gender': 'MALE',
            'date_of_birth': '1990-01-01',
            'agree_to_terms_at': '2021-09-26T05:11:09.597336+00:00',
        })
        self.assertEqual(response.status_code, 201)

    def test_post_user_profile_should_replace_previous_submission(self):
        response_one = self.client.post('/user_profiles/', {
            'name': 'Mr Green',
            'gender': 'MALE',
            'date_of_birth': '1990-01-01',
            'agree_to_terms_at': '2021-09-26T05:11:09.597336+00:00',
        })
        response_two = self.client.post('/user_profiles/', {
            'name': 'Ms Red',
            'gender': 'FEMALE',
            'date_of_birth': '1990-01-01',
            'agree_to_terms_at': '2021-09-26T05:11:09.597336+00:00',
        })
        response_data = response_two.json()
        self.assertEqual(response_one.status_code, 201)
        self.assertEqual(response_two.status_code, 201)
        self.assertEqual(response_data["name"], "Ms Red")
        self.assertEqual(response_data["gender"], "FEMALE")
        self.assertEqual(response_data["date_of_birth"], "1990-01-01")
        self.assertEqual(response_data["agree_to_terms_at"], "2021-09-26T05:11:09.597336Z")
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_patch_user_profile_should_edit_previous_submission(self):
        response_one = self.client.post('/user_profiles/', {
            'name': 'Mr Green',
            'gender': 'MALE',
            'date_of_birth': '1990-01-01',
            'agree_to_terms_at': '2021-09-26T05:11:09.597336+00:00',
        })
        response_two = self.client.patch(f'/user_profiles/{self.user.id}/', {
            'name': 'Mrs Blue',
            'date_of_birth': '1999-12-12',
            'gender': 'FEMALE',
        })
        response_data = response_two.json()
        self.assertEqual(response_one.status_code, 201)
        self.assertEqual(response_two.status_code, 200)
        self.assertEqual(response_data["name"], "Mrs Blue")
        self.assertEqual(response_data["gender"], "FEMALE")
        self.assertEqual(response_data["date_of_birth"], "1999-12-12")
        self.assertEqual(response_data["agree_to_terms_at"], "2021-09-26T05:11:09.597336Z")


class PhoneNumberChangeRequestTests(TestCase):
    def setUp(self) -> None:
        message_create_patcher = patch.object(hera.thirdparties.messagebird_client, 'message_create', return_value=None)
        self.addCleanup(message_create_patcher.stop)
        self.mock_message_create = message_create_patcher.start()
        self.user = User.objects.create(
            username="+6590000000",
        )
        self.mock_now = datetime(2021, 10, 7, 23, 59, 59, tzinfo=pytz.UTC)
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=self.mock_now)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)

    def test_create_change_request(self):
        change_request = PhoneNumberChangeRequest.objects.create(
            user=self.user,
            new_phone_number="+6591111111"
        )
        self.assertIsNotNone(change_request.id)
        self.assertIsNotNone(change_request.new_phone_number)
        self.assertIsNotNone(change_request.secret)
        self.assertEqual(len(change_request.secret), HERA_OTP_LENGTH)
        self.assertIsNotNone(change_request.expires_at)
        self.assertIsNone(change_request.solved_at)
        self.assertIsNotNone(change_request.created_at)
        self.assertIsNotNone(change_request.updated_at)

    def test_attempt_solve_change_request_when_secret_is_wrong_should_throw(self):
        change_request = PhoneNumberChangeRequest.objects.create(
            user=self.user,
            new_phone_number="+6591111111",
            secret="00000000"
        )
        with self.assertRaisesMessage(ValidationError, "Incorrect secret"):
            change_request.attempt_solve("11111111")

    def test_attempt_solve_change_request_when_expired_should_throw(self):
        change_request = PhoneNumberChangeRequest.objects.create(
            user=self.user,
            new_phone_number="+6591111111",
            secret="00000000",
            expires_at=(self.mock_now - timedelta(minutes=1))
        )
        with self.assertRaisesMessage(ValidationError, "Challenge is expired"):
            change_request.attempt_solve("11111111")

    def test_attempt_solve_change_request_when_secret_is_correct_should_succeed(self):
        change_request = PhoneNumberChangeRequest.objects.create(
            user=self.user,
            new_phone_number="+6591111111",
            secret="00000000"
        )
        change_request.attempt_solve("00000000")
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "+6591111111")
        self.assertEqual(change_request.solved_at, self.mock_now)

    def test_attempt_solve_change_request_when_number_is_taken_should_throw(self):
        change_request = PhoneNumberChangeRequest.objects.create(
            user=self.user,
            new_phone_number="+6591111111",
            secret="00000000"
        )
        _ = User.objects.create(
            username="+6591111111",
        )
        with self.assertRaisesMessage(IntegrityError, 'unique constraint "auth_user_username_key"'):
            change_request.attempt_solve("00000000")


class PhoneNumberChangeRequestViewTests(TestCase):
    def setUp(self) -> None:
        message_create_patcher = patch.object(hera.thirdparties.messagebird_client, 'message_create', return_value=None)
        self.addCleanup(message_create_patcher.stop)
        self.mock_message_create = message_create_patcher.start()
        self.throttle_patcher = patch.object(ChangePhoneNumberRequestThrottle, 'get_cache_key', return_value=None)
        self.addCleanup(self.throttle_patcher.stop)
        self.throttle_patcher.start()
        self.factory = APIRequestFactory()
        self.user = User.objects.create(
            username="+6590000000",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_change_requests_should_return_empty(self):
        response = self.client.get('/phone_number_change_requests/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_list_change_requests_should_return_existing_request(self):
        _ = PhoneNumberChangeRequest.objects.create(
            user=self.user,
            new_phone_number="+6591111111",
        )
        response = self.client.get('/phone_number_change_requests/')
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["new_phone_number"], "+6591111111")
        self.assertTrue('expires_at' in response_data[0])
        self.assertTrue('id' in response_data[0])
        self.assertFalse('secret' in response_data[0])

    def test_get_change_request_should_succeed(self):
        change_request = PhoneNumberChangeRequest.objects.create(
            user=self.user,
            new_phone_number="+6591111111",
        )
        response = self.client.get(f'/phone_number_change_requests/{change_request.id}/')
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["new_phone_number"], "+6591111111")

    def test_post_change_request_should_succeed(self):
        response = self.client.post('/phone_number_change_requests/', {
            'new_phone_number': '+6591111111',
        })
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertIsNotNone(response_data["new_phone_number"])
        self.assertIsNotNone(response_data["expires_at"])

    def test_post_change_request_when_phone_is_taken_should_fail(self):
        _ = User.objects.create(username='+6591111111')
        response = self.client.post('/phone_number_change_requests/', {
            'new_phone_number': '+6591111111',
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Phone number is already taken", status_code=400)

    def test_post_change_request_should_send_sms_via_messagebird(self):
        response = self.client.post('/phone_number_change_requests/', {
            'new_phone_number': '+6591111111',
        })
        change_request = PhoneNumberChangeRequest.objects.filter(user=self.user).first()
        self.assertEqual(response.status_code, 201)
        self.mock_message_create.assert_called_once()
        self.mock_message_create.assert_called_with(
            "HERA",
            "+6591111111",
            "Enter code %(secret)s to edit your phone number on HERA app. Do not share this code with anyone." % {
                "secret": change_request.secret,
            },
        )

    def test_resend_otp_should_send_sms_via_messagebird(self):
        create_response = self.client.post('/phone_number_change_requests/', {
            'new_phone_number': '+6591111111',
        })
        change_request_id = create_response.json()["id"]
        resend_otp_response = self.client.post(f'/phone_number_change_requests/{change_request_id}/resend_otp/')
        change_request = PhoneNumberChangeRequest.objects.get(pk=change_request_id)
        self.assertEqual(resend_otp_response.status_code, 200)
        self.assertEqual(self.mock_message_create.call_count, 2)
        self.mock_message_create.assert_called_with(
            "HERA",
            "+6591111111",
            "Enter code %(secret)s to edit your phone number on HERA app. Do not share this code with anyone." % {
                "secret": change_request.secret,
            },
        )

    def test_resend_otp_should_throttle_one_per_minute_per_phone_number(self):
        create_response = self.client.post('/phone_number_change_requests/', {
            'new_phone_number': '+6591111111',
        })
        change_request_id = create_response.json()["id"]
        resend_otp_response_one = self.client.post(f'/phone_number_change_requests/{change_request_id}/resend_otp/')
        resend_otp_response_two = self.client.post(f'/phone_number_change_requests/{change_request_id}/resend_otp/')
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(resend_otp_response_one.status_code, 200)
        self.assertEqual(resend_otp_response_two.status_code, 429)

    def test_attempt_solve_should_succeed(self):
        create_response = self.client.post('/phone_number_change_requests/', {
            'new_phone_number': '+6591111111',
        })
        change_request_id = create_response.json()["id"]
        change_request = PhoneNumberChangeRequest.objects.get(pk=change_request_id)
        attempt_solve_response = self.client.post(f'/phone_number_change_requests/{change_request_id}/attempt_solve/', {
            'guess_secret': change_request.secret,
        })
        self.assertEqual(attempt_solve_response.status_code, 200)

    def test_attempt_solve_incorrect_secret_should_fail(self):
        create_response = self.client.post('/phone_number_change_requests/', {
            'new_phone_number': '+6591111112',
        })
        change_request_id = create_response.json()["id"]
        change_request = PhoneNumberChangeRequest.objects.get(pk=change_request_id)
        wrong_secret = str(int(change_request.secret) + 1)[:HERA_OTP_LENGTH]
        attempt_solve_response = self.client.post(
            f'/phone_number_change_requests/{change_request_id}/attempt_solve/', {
                'guess_secret': wrong_secret,
            })
        self.assertContains(attempt_solve_response, "Incorrect secret", status_code=400)


class UserViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(
            username="+65912345678",
        )
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_user_profile_should_return_404(self):
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 404)

    def test_get_user_by_id_should_return_404(self):
        user_id = self.user.id
        response = self.client.get(f'/users/{user_id}/')
        self.assertEqual(response.status_code, 404)

    def test_get_user_me_should_return_user_info(self):
        response = self.client.get('/users/me/')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual("+65912345678", response_data["phone_full_number"])
        self.assertEqual("65", response_data["phone_country_code"])
        self.assertEqual("912345678", response_data["phone_national_number"])
        self.assertEqual(self.user.id, response_data["id"])
        self.assertEqual(self.user.is_staff, response_data["is_staff"])
        self.assertIsNotNone(response_data["date_joined"])
        self.assertFalse("password" in response_data)


class OnboardingProgressViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(
            username="+6590000000",
        )
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_onboarding_progresses_should_return_empty(self):
        response = self.client.get('/onboarding_progresses/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_list_onboarding_progress_should_return_existing_item(self):
        _ = OnboardingProgress.objects.create(
            user=self.user,
            has_filled_profile=True,
        )
        response = self.client.get('/onboarding_progresses/')
        response_data = response.content
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response_data, [{
            'has_filled_profile': True,
            'has_filled_pregnancy_status': False,
            'has_filled_children_info': False,
        }])

    def test_get_onboarding_progress_should_return_correct_data(self):
        _ = OnboardingProgress.objects.create(
            user=self.user,
            has_filled_profile=True,
        )
        response = self.client.get(f'/onboarding_progresses/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        response_data = response.content
        self.assertJSONEqual(response_data, {
            'has_filled_profile': True,
            'has_filled_pregnancy_status': False,
            'has_filled_children_info': False,
        })

    def test_post_onboarding_progress_should_succeed(self):
        response = self.client.post('/onboarding_progresses/', {
            'has_filled_profile': True,
            'has_filled_pregnancy_status': True,
            'has_filled_children_info': True,
        })
        self.assertEqual(response.status_code, 201)
        response_data = response.content
        self.assertJSONEqual(response_data, {
            'has_filled_profile': True,
            'has_filled_pregnancy_status': True,
            'has_filled_children_info': True,
        })
