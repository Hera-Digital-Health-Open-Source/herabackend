from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from hera.settings import HERA_OTP_LENGTH
from otp_auth.utils import generate_secret, sanitize_phone_number
from user_profile.models import PhoneNumberChangeRequest


@receiver(pre_save, sender=PhoneNumberChangeRequest)
def fill_phone_number_change_request_fields_on_create(sender, instance: PhoneNumberChangeRequest, **kwargs):
    if instance.pk is not None:
        return
    instance.new_phone_number = sanitize_phone_number(instance.new_phone_number)
    if User.objects.filter(username__exact=instance.new_phone_number).exists():
        raise ValidationError("Phone number is already taken")
    if instance.secret is None or len(instance.secret) == 0:
        instance.secret = generate_secret(HERA_OTP_LENGTH)
    if instance.expires_at is None:
        instance.expires_at = timezone.now() + timedelta(minutes=10)


@receiver(post_save, sender=PhoneNumberChangeRequest)
def send_phone_number_change_request_otp_after_create(sender, instance: PhoneNumberChangeRequest, created: bool,
                                                      raw: bool, **kwargs):
    if raw or not created:
        return
    instance.send_otp_via_sms()
