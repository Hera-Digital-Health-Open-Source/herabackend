import datetime
import heapq
from collections.abc import Iterator
from math import ceil, floor
from typing import Dict, List

from django.contrib.auth.models import User
from django.utils import timezone

from child_health.models import Child, Pregnancy, Vaccine, VaccineDose
from events.constants import CalendarEventType
from events.protocols import CalendarEventProtocol


PRENATAL_CHECKUP_WEEKS = [10, 24, 34, 38]
MAX_PREGNANCY_WEEKS = 42


def generate_prenatal_checkup_weeks(pregnancy: Pregnancy) -> Iterator[int]:
    start_date = pregnancy.estimated_start_date
    now = pregnancy.created_at
    preg_duration = now.date() - start_date
    preg_weeks = ceil(preg_duration.days / 7)
    declared_number_of_visits = pregnancy.declared_number_of_prenatal_visits

    # LATE DECLARATION PRECHECK
    # User declaring pregnancy after last checkup supposed to happen
    # will be scheduled to do one checkup the immediately following week
    if preg_weeks >= PRENATAL_CHECKUP_WEEKS[-1]:
        return [preg_weeks + 1]

    try:
        supposed_number_of_completed_visits = next(i for i, w in enumerate(PRENATAL_CHECKUP_WEEKS) if w > preg_weeks)
    except StopIteration:
        supposed_number_of_completed_visits = len(PRENATAL_CHECKUP_WEEKS)

    # len(result) >= 1. Otherwise, the function would have returned due to LATE DECLARATION PRECHECK.
    result = PRENATAL_CHECKUP_WEEKS[supposed_number_of_completed_visits:]

    deficit_number_of_visits = supposed_number_of_completed_visits - declared_number_of_visits
    accelerated_visits = []
    timelines = [preg_weeks, *result, MAX_PREGNANCY_WEEKS]
    for i in range(deficit_number_of_visits):
        if i + 1 >= len(timelines):
            break
        accelerated_visits.append(floor((timelines[i] + timelines[i + 1]) / 2))

    result += accelerated_visits
    result.sort()
    return result


class PrenatalCheckupEvent(CalendarEventProtocol):
    __slots__ = ['pregnancy', 'date', 'weeks_pregnant']

    pregnancy: Pregnancy
    date: datetime.date
    weeks_pregnant: int

    def __init__(self, pregnancy: Pregnancy, date: datetime.date, weeks_pregnant: int):
        self.pregnancy = pregnancy
        self.date = date
        self.weeks_pregnant = weeks_pregnant

    def to_dictionary(self):
        return {
            'pregnancy_id': self.pregnancy.id,
            'date': self.date,
            'weeks_pregnant': self.weeks_pregnant,
            'event_type': CalendarEventType.PRENATAL_CHECKUP.value,
        }

    def get_event_key(self):
        return f"prenatal-checkup/pregnancy-{self.pregnancy.id}/week-{self.weeks_pregnant}"


def generate_prenatal_checkup_events(pregnancy: Pregnancy) -> Iterator[PrenatalCheckupEvent]:
    checkup_weeks = generate_prenatal_checkup_weeks(pregnancy)
    pregnancy_start_date = pregnancy.estimated_start_date
    for weeks_pregnant in checkup_weeks:
        checkup_date = pregnancy_start_date + datetime.timedelta(weeks=weeks_pregnant)
        # Set to Monday
        checkup_date -= datetime.timedelta(days=checkup_date.weekday())
        yield PrenatalCheckupEvent(
            pregnancy,
            checkup_date,
            weeks_pregnant,
        )


class VaccinationEvent(CalendarEventProtocol):
    __slots__ = ['date', 'doses', 'child']

    date: datetime.date
    doses: [VaccineDose]
    child: Child

    def __init__(self, date: datetime.date, doses: [VaccineDose], child: Child):
        self.date = date
        self.doses = doses
        self.child = child

    @property
    def week_age(self) -> int:
        return self.doses[0].week_age

    def to_dictionary(self):
        return {
            'event_key': self.get_event_key(),
            'date': self.date,
            'week_age': self.week_age,
            'person_name': self.child.name,
            'vaccine_names': [dose.vaccine.friendly_name() for dose in self.doses],
            'event_type': CalendarEventType.VACCINATION.value,
            'child_id': self.child.id,
            'dose_ids': [dose.id for dose in self.doses]
        }

    def get_event_key(self):
        dose_ids = ','.join([str(dose.id) for dose in self.doses])
        return f"vaccination/child-{self.child.id}/doses-{dose_ids}"


def generate_vaccination_events_for_child(child: Child) -> Iterator[VaccinationEvent]:
    doses_query = VaccineDose.objects.filter(vaccine__is_active=True)
    if child.gender == Child.ChildGender.MALE:
        doses_query = doses_query.filter(vaccine__applicable_for_male=True)
    elif child.gender == Child.ChildGender.FEMALE:
        doses_query = doses_query.filter(vaccine__applicable_for_female=True)
    else:
        assert False, f"Unknown gender {child.gender}"
    doses_query = doses_query.prefetch_related('vaccine')
    doses_query = doses_query.order_by('week_age', 'vaccine_id', 'id')
    current_event_doses = []
    current_event_date = None
    for dose in doses_query:
        vaccination_date = child.date_of_birth + datetime.timedelta(weeks=dose.week_age)
        if current_event_date is not None and vaccination_date != current_event_date:
            yield VaccinationEvent(
                date=current_event_date,
                doses=current_event_doses,
                child=child,
            )
            current_event_doses = []
        current_event_doses.append(dose)
        current_event_date = vaccination_date
    if len(current_event_doses) > 0:
        yield VaccinationEvent(
            date=current_event_date,
            doses=current_event_doses,
            child=child,
        )



def generate_calendar_events_for_user(user: User) -> Iterator[CalendarEventProtocol]:
    def get_event_date(event):
        return event.date

    pregnancies = user.pregnancy_set.all()
    event_generators = []
    for pregnancy in pregnancies:
        event_generators.append(generate_prenatal_checkup_events(pregnancy))
    children = user.child_set.all()
    for child in children:
        event_generators.append(generate_vaccination_events_for_child(child))
    for event in heapq.merge(*event_generators, key=get_event_date):
        yield event
