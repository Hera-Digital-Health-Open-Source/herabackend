from datetime import date, timedelta, datetime

import django.utils.timezone


# Common
def calculate_delivery_date_from_start_date(start_date: date) -> date:
    result = start_date + timedelta(weeks=40)
    if result <= django.utils.timezone.now().date():
        next_week = django.utils.timezone.now() + timedelta(weeks=1)
        result = next_week.date()
    return result


# Pregnancy Week
def calculate_start_date_by_pregnancy_week(pregnancy_week: int) -> date:
    assert(pregnancy_week >= 0)
    assert(pregnancy_week < 43)
    now = django.utils.timezone.now()
    start_of_pregnancy = now - timedelta(weeks=pregnancy_week)
    return start_of_pregnancy.date()


def calculate_delivery_date_by_pregnancy_week(pregnancy_week: int) -> date:
    start_date = calculate_start_date_by_pregnancy_week(pregnancy_week)
    return calculate_delivery_date_from_start_date(start_date)


# Last Menstrual Period
def calculate_start_date_by_date_of_last_menstrual_period(last_menstrual_date: date) -> date:
    return last_menstrual_date


def calculate_delivery_date_by_date_of_last_menstrual_period(last_menstrual_date: date) -> date:
    start_date = calculate_start_date_by_date_of_last_menstrual_period(last_menstrual_date)
    return calculate_delivery_date_from_start_date(start_date)

