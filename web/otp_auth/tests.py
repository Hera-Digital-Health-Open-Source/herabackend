import random
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory

import hera.thirdparties
from hera.settings import HERA_OTP_LENGTH
from otp_auth.exceptions import InvalidPhoneNumberException
from otp_auth.models import SmsOtpChallenge
from otp_auth.views import AttemptChallengeView, CheckRegistrationView, RequestChallengeView
from user_profile.models import UserProfile


class SmsOtpChallengeTestCase(TestCase):
    def test_make_challenge_invalid_phone_number_should_throw(self):
        with self.assertRaisesMessage(InvalidPhoneNumberException, "Missing or invalid default region."):
            _ = SmsOtpChallenge.objects.make_challenge("12345678")

    def test_make_challenge_number_too_short_should_throw(self):
        with self.assertRaisesMessage(InvalidPhoneNumberException, "The text you entered is not a valid phone number"):
            _ = SmsOtpChallenge.objects.make_challenge("+62123456")

    def test_make_challenge_valid_phone_number_should_succeed(self):
        challenge = SmsOtpChallenge.objects.make_challenge("+6591234567")
        self.assertEqual(challenge.phone_number, "+6591234567")

    def test_make_challenge_dirty_phone_number_should_be_cleaned(self):
        challenge = SmsOtpChallenge.objects.make_challenge("+65 (912)3 4567")
        self.assertEqual(challenge.phone_number, "+6591234567")

    def test_make_challenge_should_generate_unique_eight_digits_otp(self):
        challenge_one = SmsOtpChallenge.objects.make_challenge("+6591234567")
        challenge_two = SmsOtpChallenge.objects.make_challenge("+6598765432")
        self.assertEqual(len(challenge_one.secret), HERA_OTP_LENGTH)
        self.assertEqual(len(challenge_two.secret), HERA_OTP_LENGTH)
        self.assertNotEqual(challenge_one.secret, challenge_two.secret)

    def test_make_challenge_should_generate_numeric_only_otp(self):
        challenge = SmsOtpChallenge.objects.make_challenge("+6591234567")
        # will throw ValueError if not valid integer
        numeric_secret = int(challenge.secret)
        self.assertIsNotNone(numeric_secret)

    def test_make_challenge_should_expire_in_ten_minutes(self):
        now = timezone.now()
        challenge = SmsOtpChallenge.objects.make_challenge("+6591234567")
        delta_to_expiry = challenge.expires_at - now
        self.assertGreaterEqual(delta_to_expiry, timedelta(minutes=10))
        self.assertLessEqual(delta_to_expiry, timedelta(minutes=11))


class RequestChallengeViewTestCase(TestCase):
    def setUp(self) -> None:
        message_create_patcher = patch.object(hera.thirdparties.messagebird_client, 'message_create', return_value=None)
        self.addCleanup(message_create_patcher.stop)
        self.mock_message_create = message_create_patcher.start()
        self.factory = APIRequestFactory()
        self.view = RequestChallengeView.as_view()

    def test_message_create_patching_success(self):
        self.assertIs(hera.thirdparties.messagebird_client.message_create, self.mock_message_create)

    def test_request_challenge(self):
        request = self.factory.post('/otp_auth/request_challenge', {
            'phone_number': '+6591234567',
        })
        response = self.view(request)
        self.assertEqual(response.status_code, 201)

    def test_request_challenge_invalid_phone_number(self):
        request = self.factory.post('/otp_auth/request_challenge', {
            'phone_number': '1234567',
        })
        response = self.view(request)
        self.assertEqual(response.status_code, 400)

    def test_request_challenge_throttle_two_per_minute_per_phone_number(self):
        request = self.factory.post('/otp_auth/request_challenge', {
            'phone_number': '+6598765432',
        })
        response_one = self.view(request)
        response_two = self.view(request)
        response_three = self.view(request)
        self.assertEqual(response_one.status_code, 201)
        self.assertEqual(response_two.status_code, 201)
        self.assertEqual(response_three.status_code, 429)

    def test_request_challenge_should_send_sms_via_messagebird(self):
        request = self.factory.post('/otp_auth/request_challenge', {
            'phone_number': '+6591234567',
        })
        _ = self.view(request)
        challenge = SmsOtpChallenge.objects.last()
        self.mock_message_create.assert_called_with(
            "HERA",
            "+6591234567",
            "Enter code %(secret)s to login to HERA app. Do not share this code with anyone." % {
                "secret": challenge.secret,
            },
        )

    def test_request_challenge_to_us_number_should_use_us_sender(self):
        request = self.factory.post('/otp_auth/request_challenge', {
            'phone_number': '+12078329519',
        })
        _ = self.view(request)
        challenge = SmsOtpChallenge.objects.last()
        self.mock_message_create.assert_called_with(
            "+12076722988",
            "+12078329519",
            "Enter code %(secret)s to login to HERA app. Do not share this code with anyone." % {
                "secret": challenge.secret,
            },
        )

class AttemptChallengeViewSignUpTestCase(TestCase):

    def setUp(self) -> None:
        phone_suffix = random.randint(0, 9999)
        self.phone_number = f"+659000{phone_suffix:04}"
        self.valid_challenge = SmsOtpChallenge.objects.create(
            phone_number=self.phone_number,
            secret="11111111",
            expires_at=(timezone.now() + timedelta(minutes=1))
        )
        self.expired_challenge = SmsOtpChallenge.objects.create(
            phone_number=self.phone_number,
            secret="00000000",
            expires_at=(timezone.now() - timedelta(seconds=1))
        )
        self.factory = APIRequestFactory()
        self.view = AttemptChallengeView.as_view()

    def test_attempt_challenge_without_phone_number_should_fail(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'secret': "12345678",
        })
        response = self.view(request)
        self.assertContains(response, "phone_number", status_code=400)

    def test_attempt_challenge_without_secret_should_fail(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
        })
        response = self.view(request)
        self.assertContains(response, "secret", status_code=400)

    def test_attempt_challenge_wrong_otp_should_reject(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': "12345678",
        })
        response = self.view(request)
        self.assertEqual(response.status_code, 401)

    def test_attempt_challenge_expired_otp_should_reject(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.expired_challenge.secret,
        })
        response = self.view(request)
        self.assertEqual(response.status_code, 401)

    def test_attempt_challenge_correct_otp_should_accept(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.valid_challenge.secret,
        })
        response = self.view(request)
        self.assertEqual(response.status_code, 201)

    def test_attempt_challenge_correct_otp_can_only_redeem_once(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.valid_challenge.secret,
        })
        response_one = self.view(request)
        response_two = self.view(request)
        self.assertEqual(response_one.status_code, 201)
        self.assertEqual(response_two.status_code, 401)

    def test_attempt_challenge_throttle_two_per_minute_per_phone_number(self):
        request = self.factory.post('/otp_auth/request_challenge', {
            'phone_number': self.phone_number,
            'secret': self.expired_challenge.secret,
        })
        response_one = self.view(request)
        response_two = self.view(request)
        response_three = self.view(request)
        self.assertEqual(response_one.status_code, 401)
        self.assertEqual(response_two.status_code, 401)
        self.assertEqual(response_three.status_code, 429)

    def test_attempt_challenge_correct_otp_gets_valid_token(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.valid_challenge.secret,
        })
        response = self.view(request)
        response_token = response.data["token"]
        is_valid_token = Token.objects.filter(
            key__exact=response_token,
        ).exists()
        self.assertTrue(is_valid_token)
        self.assertEqual(response.status_code, 201)

    def test_attempt_challenge_sign_up_should_indicate_is_new_user(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.valid_challenge.secret,
        })
        response = self.view(request)
        self.assertTrue(response.data["is_new_user"])

    def test_attempt_challenge_sign_up_should_have_null_user_profile(self):
        request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.valid_challenge.secret,
        })
        response = self.view(request)
        self.assertIsNone(response.data["user_profile"])


class AttemptChallengeViewSignInTestCase(TestCase):

    def setUp(self) -> None:
        phone_suffix = random.randint(0, 9999)
        self.phone_number = f"+659000{phone_suffix:04}"
        self.sign_up_challenge = SmsOtpChallenge.objects.create(
            phone_number=self.phone_number,
            secret="11111111",
            expires_at=(timezone.now() + timedelta(minutes=1))
        )
        self.sign_in_challenge = SmsOtpChallenge.objects.create(
            phone_number=self.phone_number,
            secret="22222222",
            expires_at=(timezone.now() + timedelta(minutes=1))
        )
        self.factory = APIRequestFactory()
        self.view = AttemptChallengeView.as_view()

    def test_attempt_challenge_sign_in_should_indicate_is_not_new_user(self):
        sign_up_request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.sign_up_challenge.secret,
        })
        sign_up_response = self.view(sign_up_request)
        sign_in_request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.sign_in_challenge.secret,
        })
        sign_in_response = self.view(sign_in_request)
        self.assertFalse(sign_in_response.data["is_new_user"])

    def test_attempt_challenge_sign_in_has_profile_should_return_profile(self):
        sign_up_request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.sign_up_challenge.secret,
        })
        sign_up_response = self.view(sign_up_request)
        user_id = sign_up_response.data["user_id"]
        user_profile = UserProfile.objects.create(
            user_id=user_id,
            name="Foo",
            gender=UserProfile.Gender.MALE,
            date_of_birth="1999-01-01",
            agree_to_terms_at=timezone.now(),
        )
        sign_in_request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.sign_in_challenge.secret,
        })
        sign_in_response = self.view(sign_in_request)
        self.assertIsNotNone(sign_in_response.data["user_profile"])
        self.assertEqual(sign_in_response.data["user_profile"]["name"], "Foo")

    def test_attempt_challenge_sign_in_no_profile_should_return_null_profile(self):
        sign_up_request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.sign_up_challenge.secret,
        })
        sign_up_response = self.view(sign_up_request)
        user_id = sign_up_response.data["user_id"]
        sign_in_request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.sign_in_challenge.secret,
        })
        sign_in_response = self.view(sign_in_request)
        self.assertIsNone(sign_in_response.data["user_profile"])
        self.assertEqual(sign_in_response.data["user_id"], user_id)

    def test_attempt_challenge_sign_in_should_invalidate_old_token(self):
        sign_up_request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.sign_up_challenge.secret,
        })
        sign_up_response = self.view(sign_up_request)
        self.assertTrue(Token.objects.filter(key=sign_up_response.data["token"]).exists())
        sign_in_request = self.factory.post('/otp_auth/attempt_challenge', {
            'phone_number': self.phone_number,
            'secret': self.sign_in_challenge.secret,
        })
        sign_in_response = self.view(sign_in_request)
        self.assertFalse(Token.objects.filter(key=sign_up_response.data["token"]).exists())
        self.assertTrue(Token.objects.filter(key=sign_in_response.data["token"]).exists())


class CheckRegistrationViewTestCase(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.view = CheckRegistrationView.as_view()

    def test_check_non_existing_phone(self):
        request = self.factory.get('/otp_auth/check_registration', {
            'phone_number': '+6590000000',
        })
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["is_registered"], False)
        self.assertEqual(response.data["phone_number"], "+6590000000")

    def test_check_existing_user(self):
        user = User.objects.create(
            username="+6590000000",
        )
        request = self.factory.get('/otp_auth/check_registration', {
            'phone_number': '+6590000000',
        })
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["is_registered"], True)
        self.assertEqual(response.data["phone_number"], "+6590000000")
