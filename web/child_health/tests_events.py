from datetime import datetime
from unittest.mock import patch

import django.utils.timezone
import pytz
from django.contrib.auth.models import User
from django.test import TestCase

from child_health.models import Pregnancy, Child, Vaccine
from child_health.events import VaccinationEvent, generate_calendar_events_for_user, generate_prenatal_checkup_weeks, \
    generate_vaccination_events_for_child


class PregnancyEventGeneratorTests(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(
            username='username',
        )
        self.set_mock_time(datetime(2021, 1, 1, 0, 0, 0, tzinfo=pytz.UTC))

    def set_mock_time(self, mock_time: datetime) -> None:
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=mock_time)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)

    def test_immediately_declared_pregnancy_should_yield_standard_schedule(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=1,
            declared_number_of_prenatal_visits=0,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [10, 24, 34, 38])

    def test_missed_first_appointment_should_catch_up_before_second_appointment(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=12,
            declared_number_of_prenatal_visits=0,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [18, 24, 34, 38])

    def test_missed_first_appointment_should_catch_up_before_second_appointment_rounded_down(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=13,
            declared_number_of_prenatal_visits=0,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [18, 24, 34, 38])

    def test_missed_first_appointment_should_catch_up_before_second_appointment_no_rounding(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=14,
            declared_number_of_prenatal_visits=0,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [19, 24, 34, 38])

    def test_schedules_are_based_on_created_at_instead_of_server_time(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=13,
            declared_number_of_prenatal_visits=0,
        )
        # 7 days after pregnancy is created
        self.set_mock_time(datetime(2021, 1, 8, 0, 0, 0, tzinfo=pytz.UTC))
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [18, 24, 34, 38])

    def test_pregnancy_declared_after_first_visit_should_yield_standard_schedule(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=14,
            declared_number_of_prenatal_visits=1,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [24, 34, 38])

    def test_declared_more_than_required_checkups_should_yield_standard_schedule(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=14,
            declared_number_of_prenatal_visits=2,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [24, 34, 38])

    def test_10_weeks_pregnant_no_checkup_should_yield_1_accelerated_visit(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=10,
            declared_number_of_prenatal_visits=0,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [17, 24, 34, 38])

    def test_24_weeks_pregnant_no_checkup_should_yield_2_accelerated_visits(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=24,
            declared_number_of_prenatal_visits=0,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [29, 34, 36, 38])

    def test_42_weeks_pregnant_3_checkups_should_yield_immediate_checkup(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=42,
            declared_number_of_prenatal_visits=3,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [43])

    def test_42_weeks_pregnant_no_checkup_should_yield_immediate_checkup(self):
        pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=42,
            declared_number_of_prenatal_visits=0,
        )
        events = list(generate_prenatal_checkup_weeks(pregnancy))
        self.assertEqual(events, [43])


class ChildVaccinationEventGeneratorTests(TestCase):
    MALE_VACCINE_FIRST_DOSE_WEEK = 1
    MALE_VACCINE_SECOND_DOSE_WEEK = 3
    FEMALE_VACCINE_FIRST_DOSE_WEEK = 2
    FEMALE_VACCINE_SECOND_DOSE_WEEK = 4
    UNIVERSAL_VACCINE_FIRST_DOSE_WEEK = 1
    UNIVERSAL_VACCINE_SECOND_DOSE_WEEK = 100

    def setUp(self) -> None:
        self.user = User.objects.create(
            username='username',
        )
        self.male_child = Child.objects.create(
            user=self.user,
            name='male_child',
            date_of_birth='2021-01-01',
            gender=Child.ChildGender.MALE,
        )
        self.male_child.refresh_from_db()
        self.female_child = Child.objects.create(
            user=self.user,
            name='female_child',
            date_of_birth='2021-01-01',
            gender=Child.ChildGender.FEMALE,
        )
        self.female_child.refresh_from_db()
        self.universal_vaccine = Vaccine.objects.create(
            name='universal_vaccine',
            nickname='UniVax',
            applicable_for_male=True,
            applicable_for_female=True,
            is_active=False,
        )
        self.universal_vaccine.vaccinedose_set.create(
            name="first dose",
            week_age=self.UNIVERSAL_VACCINE_FIRST_DOSE_WEEK,
        )
        self.universal_vaccine.vaccinedose_set.create(
            name="second dose",
            week_age=self.UNIVERSAL_VACCINE_SECOND_DOSE_WEEK,
        )
        self.male_vaccine = Vaccine.objects.create(
            name='male_vaccine',
            nickname='MaleVax',
            applicable_for_male=True,
            applicable_for_female=False,
            is_active=False,
        )
        # purposely invert dose creation order to check sorting
        self.male_vaccine.vaccinedose_set.create(
            name="second dose",
            week_age=self.MALE_VACCINE_SECOND_DOSE_WEEK,
        )
        # purposely invert dose creation order to check sorting
        self.male_vaccine.vaccinedose_set.create(
            name="first dose",
            week_age=self.MALE_VACCINE_FIRST_DOSE_WEEK,
        )
        self.female_vaccine = Vaccine.objects.create(
            name='female_vaccine',
            nickname='FemaleVax',
            applicable_for_male=False,
            applicable_for_female=True,
            is_active=False,
        )
        self.female_vaccine.vaccinedose_set.create(
            name="first dose",
            week_age=self.FEMALE_VACCINE_FIRST_DOSE_WEEK,
        )
        self.female_vaccine.vaccinedose_set.create(
            name="second dose",
            week_age=self.FEMALE_VACCINE_SECOND_DOSE_WEEK,
        )

    def test_no_active_vaccine_should_yield_empty_list(self):
        self.assertEqual([], list(generate_vaccination_events_for_child(self.male_child)))
        self.assertEqual([], list(generate_vaccination_events_for_child(self.female_child)))

    def test_male_vaccine_should_apply_to_male_child(self):
        self.male_vaccine.is_active = True
        self.male_vaccine.save()

        result = list(generate_vaccination_events_for_child(self.male_child))

        self.assertEqual(2, len(result))
        self.assertEqual(self.MALE_VACCINE_FIRST_DOSE_WEEK, result[0].week_age)
        self.assertEqual("first dose", result[0].doses[0].name)
        self.assertEqual(self.MALE_VACCINE_SECOND_DOSE_WEEK, result[1].week_age)
        self.assertEqual("second dose", result[1].doses[0].name)

    def test_female_vaccine_should_not_apply_to_male_child(self):
        self.female_vaccine.is_active = True
        self.female_vaccine.save()
        self.assertEqual([], list(generate_vaccination_events_for_child(self.male_child)))


class ChildHealthGenerateCalendarEventTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(
            username='username',
        )
        self.mock_now = datetime(2021, 6, 1, 0, 0, 0, tzinfo=pytz.UTC)
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=self.mock_now)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)
        self.male_child = Child.objects.create(
            user=self.user,
            name='male_child',
            date_of_birth='2021-01-01',
            gender=Child.ChildGender.MALE,
        )
        self.male_child.refresh_from_db()
        self.universal_vaccine = Vaccine.objects.create(
            name='universal_vaccine',
            nickname='UniVax',
            applicable_for_male=True,
            applicable_for_female=True,
            is_active=True,
        )
        self.universal_vaccine.vaccinedose_set.create(
            name="first dose",
            week_age=0,
        )
        self.universal_vaccine.vaccinedose_set.create(
            name="second dose",
            week_age=52,
        )
        self.pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=42,
            declared_number_of_prenatal_visits=0,
        )

    def test_calendar_event_generator(self):
        events = list(generate_calendar_events_for_user(self.user))
        self.assertEqual(len(events), 3)
        self.assertTrue(all(events[i].date < events[i+1].date for i in range(len(events) - 1)))
