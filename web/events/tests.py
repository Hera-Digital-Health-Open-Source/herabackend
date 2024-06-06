import httpx
import pytz
import django.utils.timezone
import pytz

from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.db.transaction import atomic
from onesignal_sdk.response import OneSignalResponse

from child_health.models import Pregnancy, Child, Vaccine, VaccineDose
from child_health.events import PrenatalCheckupEvent, VaccinationEvent
from events.constants import CalendarEventType
from events.models import NotificationEvent, NotificationSchedule, NotificationType, NotificationTemplate, LanguageCode
from events.utils import generate_notification_events_for_calendar_event, generate_notification_events_for_all_users, generate_notification_events_for_user
import hera.thirdparties
from user_profile.models import UserProfile


class GenerateNotificationEventForPrenatalCheckupTests(TestCase):

    def setUp(self) -> None:
        self.patch_onesignal()
        self.user = User.objects.create(
            username='username',
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            name='name',
            gender=UserProfile.Gender.MALE,
            date_of_birth=date(1990, 1, 1),
            agree_to_terms_at=datetime(2020, 1, 1, tzinfo=pytz.UTC),
            language_code=UserProfile.LanguageCode.EN,
            timezone='UTC',
        )
        self.type_one_week_before = NotificationType.objects.create(
            code='prenatalcheckup.one_week_before',
            description='description',
        )
        self.schedule_one_week_before = NotificationSchedule.objects.create(
            notification_type=self.type_one_week_before,
            calendar_event_type=CalendarEventType.PRENATAL_CHECKUP,
            offset_days=-7,
            time_of_day=time(10, 0),
        )
        self.type_on_the_day = NotificationType.objects.create(
            code='prenatalcheckup.on_the_day',
            description='description'
        )
        self.schedule_on_the_day = NotificationSchedule.objects.create(
            notification_type=self.type_on_the_day,
            calendar_event_type=CalendarEventType.PRENATAL_CHECKUP,
            offset_days=0,
            time_of_day=time(10, 0),
            push_time_to_live=timedelta(hours=1),
        )
        self.schedules = [self.schedule_one_week_before, self.schedule_on_the_day]
        self.pregnancy = Pregnancy(
            user=self.user,
            declared_pregnancy_week=1,
        )
        self.calendar_event = PrenatalCheckupEvent(
            pregnancy=self.pregnancy,
            date=date(2021, 1, 10),
            weeks_pregnant=1,
        )

    def patch_onesignal(self):
        patcher = patch.object(hera.thirdparties.onesignal_client, 'send_notification', return_value=OneSignalResponse(
            httpx.Response(200, text="{}")
        ))
        self.addCleanup(patcher.stop)
        _ = patcher.start()

    def set_mock_time(self, mock_time: datetime) -> None:
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=mock_time)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)

    def test_pre_9_days_generates_no_event(self):
        self.set_mock_time(datetime(2021, 1, 1, 0, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual([], result)

    def test_pre_7_days_before_10_am_generates_no_event(self):
        self.set_mock_time(datetime(2021, 1, 3, 9, 59, 59, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual([], result)

    def test_pre_7_days_at_10_am_generates_correct_event(self):
        self.set_mock_time(datetime(2021, 1, 3, 10, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(1, len(result))
        self.assertEqual(result[0].user, self.user)
        self.assertEqual(result[0].event_key, self.calendar_event.get_event_key())
        self.assertEqual(result[0].schedule, self.schedule_one_week_before)
        self.assertEqual(result[0].notification_type, self.type_one_week_before)
        self.assertIsNone(result[0].read_at)

    def test_on_the_day_before_scheduled_time_generates_no_event(self):
        self.set_mock_time(datetime(2021, 1, 10, 9, 59, 59, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(0, len(result))

    def test_on_the_day_at_scheduled_time_generates_one_event(self):
        self.set_mock_time(datetime(2021, 1, 10, 10, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(1, len(result))

    def test_on_the_day_before_ttl_expiry_generates_one_event(self):
        self.set_mock_time(datetime(2021, 1, 10, 11, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(1, len(result))

    def test_on_the_day_after_ttl_expiry_generates_no_event(self):
        self.set_mock_time(datetime(2021, 1, 10, 11, 0, 1, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(0, len(result))

    def test_prenatal_checkup_not_mixed_with_vaccination_schedule(self):
        self.set_mock_time(datetime(2021, 1, 10, 10, 0, 0, tzinfo=pytz.UTC))
        irrelevant_notif_type = NotificationType.objects.create(
            code='vacccination.on_the_day',
            description='description'
        )
        irrelevant_notif_schedule = NotificationSchedule.objects.create(
            notification_type=irrelevant_notif_type,
            calendar_event_type=CalendarEventType.VACCINATION,
            offset_days=0,
            time_of_day=time(9, 59),
            push_time_to_live=timedelta(hours=1),
        )
        irrelevant_schedules = [irrelevant_notif_schedule]
        result = list(generate_notification_events_for_calendar_event(self.user, irrelevant_schedules, self.calendar_event))
        self.assertEqual(0, len(result))

    def test_no_user_profile_should_not_crash(self):
        self.set_mock_time(datetime(2021, 1, 10, 10, 0, 0, tzinfo=pytz.UTC))
        self.user_profile.delete()
        self.user.refresh_from_db()
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(1, len(result))


class GenerateNotificationEventForVaccinationTests(TestCase):

    def setUp(self) -> None:
        self.patch_onesignal()
        self.user = User.objects.create(
            username='username',
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            name='name',
            gender=UserProfile.Gender.MALE,
            date_of_birth=date(1990, 1, 1),
            agree_to_terms_at=datetime(2020, 1, 1, tzinfo=pytz.UTC),
            language_code=UserProfile.LanguageCode.EN,
            timezone='UTC',
        )
        self.type_one_week_before = NotificationType.objects.create(
            code='vaccination.one_week_before',
            description='description',
        )
        self.schedule_one_week_before = NotificationSchedule.objects.create(
            notification_type=self.type_one_week_before,
            calendar_event_type=CalendarEventType.VACCINATION,
            offset_days=-7,
            time_of_day=time(10, 0),
        )
        self.type_on_the_day = NotificationType.objects.create(
            code='vaccination.on_the_day',
            description='description'
        )
        self.schedule_on_the_day = NotificationSchedule.objects.create(
            notification_type=self.type_on_the_day,
            calendar_event_type=CalendarEventType.VACCINATION,
            offset_days=0,
            time_of_day=time(10, 0),
            push_time_to_live=timedelta(hours=1),
        )
        self.schedules = [self.schedule_one_week_before, self.schedule_on_the_day]
        self.child = Child(
            user=self.user,
            name='name',
            date_of_birth=date(2021, 1, 1),
            gender=Child.ChildGender.MALE,
        )
        self.vaccine = Vaccine(
            name='vaccine',
            is_active=True,
        )
        self.dose = VaccineDose(
            vaccine=self.vaccine,
            name='dose 1',
            week_age=1,
        )
        self.calendar_event = VaccinationEvent(
            date=date(2021, 1, 10),
            doses=[self.dose],
            child=self.child,
        )

    def patch_onesignal(self):
        patcher = patch.object(hera.thirdparties.onesignal_client, 'send_notification', return_value=OneSignalResponse(
            httpx.Response(200, text="{}")
        ))
        self.addCleanup(patcher.stop)
        _ = patcher.start()

    def set_mock_time(self, mock_time: datetime) -> None:
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=mock_time)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)

    def test_pre_9_days_generates_no_event(self):
        self.set_mock_time(datetime(2021, 1, 1, 0, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual([], result)

    def test_pre_7_days_before_10_am_generates_no_event(self):
        self.set_mock_time(datetime(2021, 1, 3, 9, 59, 59, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual([], result)

    def test_pre_7_days_at_10_am_generates_correct_event(self):
        self.set_mock_time(datetime(2021, 1, 3, 10, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(1, len(result))
        self.assertEqual(result[0].user, self.user)
        self.assertEqual(result[0].event_key, self.calendar_event.get_event_key())
        self.assertEqual(result[0].schedule, self.schedule_one_week_before)
        self.assertEqual(result[0].notification_type, self.type_one_week_before)
        self.assertIsNone(result[0].read_at)

    def test_on_the_day_before_scheduled_time_generates_no_event(self):
        self.set_mock_time(datetime(2021, 1, 10, 9, 59, 59, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(0, len(result))

    def test_on_the_day_at_scheduled_time_generates_one_event(self):
        self.set_mock_time(datetime(2021, 1, 10, 10, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(1, len(result))

    def test_on_the_day_before_ttl_expiry_generates_one_event(self):
        self.set_mock_time(datetime(2021, 1, 10, 11, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(1, len(result))

    def test_on_the_day_after_ttl_expiry_generates_no_event(self):
        self.set_mock_time(datetime(2021, 1, 10, 11, 0, 1, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_calendar_event(self.user, self.schedules, self.calendar_event))
        self.assertEqual(0, len(result))

    def test_vaccination_not_mixed_with_vaccination_schedule(self):
        self.set_mock_time(datetime(2021, 1, 10, 10, 0, 0, tzinfo=pytz.UTC))
        irrelevant_notif_type = NotificationType.objects.create(
            code='prenatalcheckup.on_the_day',
            description='description'
        )
        irrelevant_notif_schedule = NotificationSchedule.objects.create(
            notification_type=irrelevant_notif_type,
            calendar_event_type=CalendarEventType.PRENATAL_CHECKUP,
            offset_days=0,
            time_of_day=time(9, 59),
            push_time_to_live=timedelta(hours=1),
        )
        irrelevant_schedules = [irrelevant_notif_schedule]
        result = list(generate_notification_events_for_calendar_event(self.user, irrelevant_schedules, self.calendar_event))
        self.assertEqual(0, len(result))


class GenerateNotificationEventsForAllUsersTests(TransactionTestCase):
    def setUp(self) -> None:
        self.patch_onesignal()
        self.user = User.objects.create(
            username='username',
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            name='name',
            gender=UserProfile.Gender.MALE,
            date_of_birth=date(1990, 1, 1),
            agree_to_terms_at=datetime(2020, 1, 1, tzinfo=pytz.UTC),
            language_code=UserProfile.LanguageCode.EN,
            timezone='UTC',
        )
        self.set_mock_time(datetime(2021, 6, 1, 0, 0, 0, tzinfo=pytz.UTC))
        self.male_child = Child.objects.create(
            user=self.user,
            name='male_child',
            date_of_birth='2021-06-06',
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
        self.pregnancy = Pregnancy.objects.create(
            user=self.user,
            declared_pregnancy_week=42,
            declared_number_of_prenatal_visits=0,
        )
        prenatal_notification_type = NotificationType.objects.create(
            code='prenatalcheckup.on_the_day',
            description='description'
        )
        NotificationTemplate.objects.create(
            notification_type=prenatal_notification_type,
            language_code=LanguageCode.ENGLISH,
            push_title='title',
            push_body='body',
            in_app_content='content',
        )
        NotificationSchedule.objects.create(
            notification_type=prenatal_notification_type,
            calendar_event_type=CalendarEventType.PRENATAL_CHECKUP,
            offset_days=0,
            time_of_day=time(10, 0),
            push_time_to_live=timedelta(hours=1),
        )
        vaccination_notification_type = NotificationType.objects.create(
            code='vaccination.on_the_day',
            description='description',
        )
        NotificationTemplate.objects.create(
            notification_type=vaccination_notification_type,
            language_code=LanguageCode.ENGLISH,
            push_title='title',
            push_body='body',
            in_app_content='content',
        )
        NotificationSchedule.objects.create(
            notification_type=vaccination_notification_type,
            calendar_event_type=CalendarEventType.VACCINATION,
            offset_days=0,
            time_of_day=time(10, 0),
            push_time_to_live=timedelta(days=2),
        )
        NotificationEvent.objects.all().delete()

    def patch_onesignal(self):
        patcher = patch.object(hera.thirdparties.onesignal_client, 'send_notification', return_value=OneSignalResponse(
            httpx.Response(200, text="{}")
        ))
        self.addCleanup(patcher.stop)
        _ = patcher.start()

    def set_mock_time(self, mock_time: datetime) -> None:
        timezone_now_patcher = patch.object(django.utils.timezone, 'now', return_value=mock_time)
        timezone_now_patcher.start()
        self.addCleanup(timezone_now_patcher.stop)

    def test_notification_event_generators_yield_two_events(self):
        self.set_mock_time(datetime(2021, 6, 7, 10, 0, 0, tzinfo=pytz.UTC))
        result = list(generate_notification_events_for_user(self.user, NotificationSchedule.objects.all()))
        self.assertEqual(2, len(result))

    def test_generate_notification_events_for_all_users_saves_notification_events(self):
        self.set_mock_time(datetime(2021, 6, 7, 10, 0, 0, tzinfo=pytz.UTC))
        generate_notification_events_for_all_users()
        self.assertEqual(2, NotificationEvent.objects.count())

    def test_generate_notification_events_for_all_users_sorts_notification_events(self):
        self.set_mock_time(datetime(2021, 6, 7, 10, 0, 0, tzinfo=pytz.UTC))
        generate_notification_events_for_all_users()
        notifications = NotificationEvent.objects.all()
        self.assertGreaterEqual(notifications[1].notification_available_at, notifications[0].notification_available_at)

    def test_generate_notification_events_for_all_users_twice(self):
        self.set_mock_time(datetime(2021, 6, 7, 10, 0, 0, tzinfo=pytz.UTC))
        generate_notification_events_for_all_users()
        self.set_mock_time(datetime(2021, 6, 7, 10, 1, 0, tzinfo=pytz.UTC))
        generate_notification_events_for_all_users()
        self.assertEqual(2, NotificationEvent.objects.count())