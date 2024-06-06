from datetime import date, datetime, timedelta
from unittest.mock import patch

import django.utils.timezone
import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from child_health.models import Child, Pregnancy
from child_health.utils import calculate_delivery_date_by_date_of_last_menstrual_period, \
    calculate_delivery_date_by_pregnancy_week, calculate_start_date_by_date_of_last_menstrual_period, \
    calculate_start_date_by_pregnancy_week


class PregnancyViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(
            username="+6590000000"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.mock_now = datetime(2021, 10, 7, 23, 59, 59, tzinfo=pytz.UTC)
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=self.mock_now)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)

    def test_list_pregnancy_should_return_empty(self):
        response = self.client.get('/pregnancies/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_create_pregnancy_with_pregnancy_week_should_succeed(self):
        response = self.client.post('/pregnancies/', {
            'declared_pregnancy_week': 2
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['declared_pregnancy_week'], 2)

    def test_create_pregnancy_with_date_of_last_menstrual_period_should_succeed(self):
        response = self.client.post('/pregnancies/', {
            'declared_date_of_last_menstrual_period': '2021-10-01'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['declared_date_of_last_menstrual_period'], '2021-10-01')

    def test_create_pregnancy_with_neither_pregnancy_week_nor_menstrual_period_should_fail(self):
        response = self.client.post('/pregnancies/')
        self.assertEqual(response.status_code, 400)

    def test_create_pregnancy_with_pregnancy_week_should_calculate_start_and_delivery_date(self):
        response = self.client.post('/pregnancies/', {
            'declared_pregnancy_week': 1,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['estimated_start_date'], '2021-09-30')
        self.assertEqual(response.data['estimated_delivery_date'], '2022-07-07')

    def test_create_pregnancy_with_date_of_menstrual_period_should_calculate_start_and_delivery_date(self):
        response = self.client.post('/pregnancies/', {
            'declared_date_of_last_menstrual_period': '2021-09-30',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['estimated_start_date'], '2021-09-30')
        self.assertEqual(response.data['estimated_delivery_date'], '2022-07-07')

    def test_get_active_pregnancy_should_return_404_when_no_pregnancy(self):
        response = self.client.get('/pregnancies/active/')
        self.assertEqual(response.status_code, 404)

    def test_get_active_pregnancy_should_return_404_when_no_active_pregnancy(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=42,
            declared_number_of_prenatal_visits=0,
        )
        pregnancy.estimated_delivery_date = (self.mock_now - timedelta(days=10)).date()
        pregnancy.save()
        response = self.client.get('/pregnancies/active/')
        self.assertEqual(response.status_code, 404)

    def test_get_active_pregnancy_should_return_active_pregnancy(self):
        Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=1,
            declared_number_of_prenatal_visits=0,
        )
        response = self.client.get('/pregnancies/active/')
        self.assertEqual(response.status_code, 200)


class PregnancyWeekCalculatorTests(TestCase):
    def setUp(self) -> None:
        self.mock_now = datetime(2021, 10, 7, 23, 59, 59, tzinfo=pytz.UTC)
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=self.mock_now)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)

    def test_start_date_zero_week_should_return_start_of_today(self):
        result = calculate_start_date_by_pregnancy_week(0)
        self.assertEqual(result, date(2021, 10, 7))

    def test_start_date_one_week_should_return_seven_days_ago(self):
        result = calculate_start_date_by_pregnancy_week(1)
        self.assertEqual(result, date(2021, 9, 30))

    def test_start_date_fourty_weeks_should_return_fourty_weeks_ago(self):
        result = calculate_start_date_by_pregnancy_week(40)
        self.assertEqual(result, date(2020, 12, 31))

    def test_start_date_negative_one_week_should_throw(self):
        with self.assertRaises(AssertionError):
            _ = calculate_start_date_by_pregnancy_week(-1)

    def test_start_date_fourty_one_weeks_should_throw(self):
        with self.assertRaises(AssertionError):
            _ = calculate_start_date_by_pregnancy_week(43)

    def test_delivery_date_at_zeroth_week_should_be_in_fourty_weeks(self):
        result = calculate_delivery_date_by_pregnancy_week(0)
        self.assertEqual(result, date(2022, 7, 14))

    def test_delivery_date_at_fourtieth_week_should_be_next_week(self):
        result = calculate_delivery_date_by_pregnancy_week(40)
        self.assertEqual(result, date(2021, 10, 14))

    def test_delivery_date_at_fourty_second_week_should_be_next_week(self):
        result = calculate_delivery_date_by_pregnancy_week(42)
        self.assertEqual(result, date(2021, 10, 14))


class LastMenstrualPeriodCalculatorTests(TestCase):
    def setUp(self) -> None:
        self.mock_now = datetime(2021, 10, 7, 23, 59, 59, tzinfo=pytz.UTC)
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=self.mock_now)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)

    def test_start_date_should_be_same_as_input(self):
        result = calculate_start_date_by_date_of_last_menstrual_period(date(2021, 10, 7))
        self.assertEqual(result, date(2021, 10, 7))

    def test_delivery_date_should_be_280_days_after_last_menstrual_period(self):
        result = calculate_delivery_date_by_date_of_last_menstrual_period(date(2021, 10, 7))
        self.assertEqual(result, date(2022, 7, 14))

    def test_delivery_date_at_fourtieth_week_should_be_next_week(self):
        result = calculate_delivery_date_by_date_of_last_menstrual_period(date(2020, 12, 31))
        self.assertEqual(result, date(2021, 10, 14))


class ChildrenViewTests(TestCase):
    fixtures = ['child_health/fixtures/vaccines_and_doses.json']

    def setUp(self) -> None:
        self.user = User.objects.create(
            username="+6590000000",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_child_should_succeed(self):
        response = self.client.post('/children/', {
            'name': 'Child Name',
            'date_of_birth': '2020-01-01',
            'gender': 'FEMALE',
        })
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['id'])
        self.assertEqual(response.data['name'], 'Child Name')
        self.assertEqual(response.data['date_of_birth'], '2020-01-01')
        self.assertEqual(response.data['gender'], 'FEMALE')

    def test_create_child_with_past_vaccination_should_succeed(self):
        response = self.client.post('/children/', {
            'name': 'Child Name',
            'date_of_birth': '2020-01-01',
            'gender': 'FEMALE',
            'past_vaccinations': [1],
        })
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['id'])
        self.assertEqual(response.data['name'], 'Child Name')
        self.assertEqual(response.data['date_of_birth'], '2020-01-01')
        self.assertEqual(response.data['gender'], 'FEMALE')
        self.assertEqual(response.data['past_vaccinations'], [1])

    def test_edit_child_vaccination_should_succeed(self):
        child = Child.objects.create(
            name='Child Name',
            date_of_birth='2020-01-01',
            gender=Child.ChildGender.FEMALE,
            user=self.user,
        )
        response = self.client.put(f'/children/{child.id}/', {
            'name': 'Child Name',
            'date_of_birth': '2020-01-01',
            'gender': 'FEMALE',
            'past_vaccinations': [2],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], child.id)
        self.assertEqual(response.data['name'], 'Child Name')
        self.assertEqual(response.data['date_of_birth'], '2020-01-01')
        self.assertEqual(response.data['gender'], 'FEMALE')
        self.assertEqual(response.data['past_vaccinations'], [2])


class VaccinesViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(
            username="+6590000000"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_vaccines_should_succeed(self):
        response = self.client.get('/vaccines/')
        self.assertEqual(response.status_code, 200)
