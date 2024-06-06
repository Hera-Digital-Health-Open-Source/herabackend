from django.db import models
from django.utils.translation import gettext_lazy as _


class CalendarEventType(models.TextChoices):
    PRENATAL_CHECKUP = 'prenatal_checkup', _('Prenatal Checkup')
    VACCINATION = 'vaccination', _('Vaccination')
    
