from django.db import models
from django.contrib.auth.models import User

class OptStatus(models.TextChoices):
    OPT_IN = 'opt_in'
    OPT_OUT = 'opt_out'


class Source(models.TextChoices):
    HERA_APP = 'hera_app'
    WHATSAPP = 'whatsapp'


class WhatsAppOptHistory(models.Model):
    """ Maintains a history of opt-ins and opt-outs of whatsapp notifications """
    username = models.CharField(
        max_length=150
    )
    opt_status = models.CharField(
        max_length=7,
        choices=OptStatus.choices,
    )
    opt_datetime = models.DateTimeField(auto_now_add=True)
    source = models.CharField(
        max_length=8,
        choices=Source.choices,
        default="hera_app"
    )

    class Meta:
        index_together = [
            ['username']
        ]
