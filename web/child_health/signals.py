from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from child_health.models import Pregnancy
from child_health.utils import *


@receiver(pre_save, sender=Pregnancy)
def fill_pregnancy_delivery_date(sender, instance: Pregnancy, **kwargs):
    if instance.declared_date_of_last_menstrual_period is None and instance.declared_pregnancy_week is None:
        raise ValidationError(
            detail="Either declared_date_of_last_menstrual_period or declared_pregnancy_week is required"
        )
    if instance.estimated_start_date is not None and instance.estimated_delivery_date is not None:
        return  # do not override existing value
    if instance.declared_pregnancy_week is not None:
        instance.estimated_start_date = calculate_start_date_by_pregnancy_week(instance.declared_pregnancy_week)
        instance.estimated_delivery_date = calculate_delivery_date_by_pregnancy_week(instance.declared_pregnancy_week)
    else:
        instance.estimated_start_date = calculate_start_date_by_date_of_last_menstrual_period(instance.declared_date_of_last_menstrual_period)
        instance.estimated_delivery_date = calculate_delivery_date_by_date_of_last_menstrual_period(instance.declared_date_of_last_menstrual_period)
