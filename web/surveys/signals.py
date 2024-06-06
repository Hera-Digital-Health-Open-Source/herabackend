import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
import django

from surveys.models import Survey
from surveys.utils import send_whatsapp_surveys, send_notification
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from whatsapp_opt_history.utils import is_user_opt_in

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Survey)
def send_notification_to_onesignal_and_whatsapp(sender, instance: Survey, created, **kwargs):
    if instance.is_served == True or instance.response is not None:
        return
    response = send_notification(instance.question, [str(instance.user.id)])
    whatsapp_username = instance.user.username
    sender_token = Token.objects.get_or_create(user=instance.user)

    if instance.twilio_content_sid and is_user_opt_in(whatsapp_username):
      try:
          send_whatsapp_surveys(whatsapp_username, str(instance.twilio_content_sid), instance.context, instance.id, sender_token)
      except:
          pass

    if 200 <= response.status_code <= 299 and 'errors' not in response.body:
        instance.is_served = True
        instance.available_at = django.utils.timezone.now()
        instance.save()
    else:
        logger.error(
            f"Error when sending notification event {instance.id} to OneSignal: {response.body}")
