import heapq
from collections.abc import Iterator

import django.utils.timezone
import pytz
from django.contrib.auth.models import User
from django.db import IntegrityError

from child_health.models import PastVaccination, VaccineDose
from events.protocols import CalendarEventProtocol
from events.utils import generate_all_calendar_events_for_user
from hera.utils import get_sanitized_hstore_dict
from surveys.models import Survey, SurveySchedule
import hera.thirdparties
import requests
from hera.secrets import TWILIO_MESSAGING_SERVICE_SID
from onesignal_sdk.error import OneSignalHTTPError
import json

def generate_surveys_for_calendar_event(user: User, schedules: [SurveySchedule],
                                        event: CalendarEventProtocol, force_create_surveys=False) -> \
        Iterator[Survey]:
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
        survey_available_at, survey_expires_at = schedule.get_survey_window(calendar_event_date, timezone)
        if force_create_surveys or survey_available_at <= now <= survey_expires_at:
            yield Survey(
                user=user,
                event_key=event.get_event_key(),
                schedule=schedule,
                survey_template=schedule.survey_template,
                context=get_sanitized_hstore_dict(event_dict),
                response=None,
                available_at=survey_available_at,
                expires_at=survey_expires_at,
                responded_at=None,
            )


def generate_surveys_for_user(user: User, schedules: [SurveySchedule], force_create_surveys=False) -> Iterator[Survey]:
    def get_survey_sort_key(survey: Survey):
        return (survey.available_at, survey.expires_at,)

    calendar_events = generate_all_calendar_events_for_user(user)
    survey_generators = \
        [generate_surveys_for_calendar_event(user, schedules, e, force_create_surveys=force_create_surveys) for e in
         calendar_events]
    for survey in heapq.merge(*survey_generators, key=get_survey_sort_key):
        yield survey


def process_survey_after_response_created(survey: Survey):
    if survey.response is None:
        return
    if survey.survey_template.code == 'vaccination.have_you_visited':
        process_vaccination_have_you_visited_survey_response(survey)


def process_vaccination_have_you_visited_survey_response(survey: Survey):
    """
    Create a PastVaccination object when user says yes to vaccination survey.
    Effectively, this "ticks the vaccination checkbox" on behalf of the user on survey response.
    Note that if user says "no", we will do no action (neither tick nor untick).
    """
    if survey.response != 'yes':
        return
    child_id_string = survey.context.get('child_id', '')
    if len(child_id_string) == 0:
        return
    child_id = int(child_id_string)
    dose_ids_string = survey.context.get('dose_ids', '')
    if len(dose_ids_string) == 0:
        return
    dose_ids = [int(dose_id) for dose_id in survey.context['dose_ids'].split(', ')]
    for dose_id in dose_ids:
        dose = VaccineDose.objects.get(pk=dose_id)
        vaccine_id = dose.vaccine_id
        try:
            PastVaccination.objects.create(child_id=child_id, vaccine_id=vaccine_id)
        except IntegrityError:
            pass

def send_whatsapp_surveys(username: str, template_name: str,  context: dict, survey_id: int, sender_token: tuple):
    response = hera.thirdparties.twilio_client.messages.create(
                              content_sid=template_name,
                              from_=TWILIO_MESSAGING_SERVICE_SID,
                              content_variables=json.dumps({
                                  '1': str(context["person_name"]),
                                  '2': str(context["vaccine_names"]),
                                  '3': str(survey_id),
                                  '4': context['vaccine_names'],
                                  '5': str(context['child_id']),
                                  '6': sender_token[0].key
                              }),
                              to='whatsapp:'+username
                          )
    return response


def send_notification(body: str, users: list):
    notification_body = {
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
