import heapq
from collections.abc import Iterator

import django.utils.timezone
import pytz
from django.contrib.auth.models import User
from django.db import IntegrityError

from child_health.events import generate_calendar_events_for_user
from events.models import NotificationEvent, NotificationSchedule
from events.protocols import CalendarEventProtocol
import hera.thirdparties
from hera.secrets import TWILIO_MESSAGING_SERVICE_SID
from onesignal_sdk.error import OneSignalHTTPError
import json


def generate_all_calendar_events_for_user(user: User) -> Iterator[CalendarEventProtocol]:
    return generate_calendar_events_for_user(user)


# Given one calendar event, generate a list of
# notification events based on admin-defined Notification Schedules
def generate_notification_events_for_calendar_event(user: User, schedules: [NotificationSchedule],
                                                    event: CalendarEventProtocol, force_create_events=False) -> \
Iterator[NotificationEvent]:
    try:
        timezone_name = user.userprofile.timezone
        timezone = pytz.timezone(timezone_name)
    except User.userprofile.RelatedObjectDoesNotExist:
        timezone = pytz.UTC
    now = django.utils.timezone.now()
    for schedule in schedules:
        event_dict = event.to_dictionary()
        if schedule.calendar_event_type != event_dict['event_type']:
            continue
        calendar_event_date = event_dict['date']
        notification_available_at, notification_expires_at = schedule.get_notification_window(calendar_event_date,
                                                                                              timezone)
        if force_create_events or notification_available_at <= now <= notification_expires_at:
            yield NotificationEvent(
                user=user,
                event_key=event.get_event_key(),
                schedule=schedule,
                context=event_dict,
                notification_type=schedule.notification_type,
                notification_available_at=notification_available_at,
                notification_expires_at=notification_expires_at,
                push_notification_sent_at=None,
            )


def generate_notification_events_for_user(user: User, schedules: [NotificationSchedule], force_create_events=False) -> \
Iterator[NotificationEvent]:
    def get_notification_sort_key(notification_event: NotificationEvent):
        return (notification_event.notification_available_at, notification_event.notification_expires_at,)

    calendar_events = generate_all_calendar_events_for_user(user)
    notification_event_generators = \
        [generate_notification_events_for_calendar_event(user, schedules, e, force_create_events=force_create_events)
         for e in calendar_events]
    for event in heapq.merge(*notification_event_generators, key=get_notification_sort_key):
        yield event


def generate_notification_events_for_all_users():
    schedules = NotificationSchedule.objects.order_by('calendar_event_type', 'offset_days', 'time_of_day').all()
    users = User.objects.filter(is_active=True).all()
    for user in users:
        notification_events = generate_notification_events_for_user(user, schedules)
        for event in notification_events:
            try:
                event.save()
            except IntegrityError:
                pass

def  send_whatsapp_message(username: str, template_name: str,  context: dict):
    content_variables = {}
    if 'event_type' in context:
        if str(context["event_type"]) == 'prenatal_checkup':
            content_variables = {
                '1': str(context["weeks_pregnant"]),
            }
        elif str(context["event_type"]) == 'vaccination':
            content_variables = {
                '1': str(context["person_name"]),
                '2': str(context["vaccine_names"]),
            }
    response = hera.thirdparties.twilio_client.messages.create(
        content_sid=template_name,
        from_=TWILIO_MESSAGING_SERVICE_SID,
        content_variables=json.dumps(content_variables),
        to='whatsapp:'+username
    )
    
    return response


def send_notification(title: str, body: str, users: list):
    notification_body = {
        'headings': {
            'en': title,
        },
        'contents': {
            'en': body,
        },
        'include_external_user_ids': users,
    }

    try:
      response = hera.thirdparties.onesignal_client.send_notification(notification_body)

      return response
    except OneSignalHTTPError:
      pass
