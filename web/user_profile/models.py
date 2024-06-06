import django.utils.timezone
import pytz
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

import hera.thirdparties


class UserProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'MALE', _('Male')
        FEMALE = 'FEMALE', _('Female')

    class LanguageCode(models.TextChoices):
        EN = 'en', 'English'
        TR = 'tr', 'Turkish'
        AR = 'ar', 'Arabic'
        PS = 'ps', 'Pashto'
        PRS = 'prs', 'Dari'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    name = models.CharField(max_length=255)
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
    )
    date_of_birth = models.DateField()
    agree_to_terms_at = models.DateTimeField()
    language_code = models.CharField(choices=LanguageCode.choices, max_length=5, default='en')
    timezone = models.CharField(
        max_length=50,
        choices=[(tz, tz) for tz in pytz.all_timezones],
        default='UTC',
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"


class PhoneNumberChangeRequest(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    new_phone_number = models.CharField(max_length=150)
    secret = models.CharField(max_length=255)
    expires_at = models.DateTimeField(blank=True, null=True)
    solved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def send_otp_via_sms(self):
        hera.thirdparties.messagebird_client.message_create(
            "HERA",
            self.new_phone_number,
            _("Enter code %(secret)s to edit your phone number on HERA app. Do not share this code with anyone.") % {
                "secret": self.secret,
            },
        )

    def attempt_solve(self, guess_secret):
        now = django.utils.timezone.now()
        if self.expires_at < now:
            raise ValidationError("Challenge is expired")
        if guess_secret != self.secret:
            raise ValidationError("Incorrect secret")
        with transaction.atomic():
            self.user.username = self.new_phone_number
            self.solved_at = now
            self.user.save()
            self.save()


class OnboardingProgress(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    has_filled_profile = models.BooleanField(
        default=False,
        help_text="Whether the user has submitted or skipped 'Complete Profile' onboarding screen",
    )
    has_filled_pregnancy_status = models.BooleanField(
        default=False,
        help_text="Whether the user has submitted or skipped 'Your Pregnancy' onboarding screen",
    )
    has_filled_children_info = models.BooleanField(
        default=False,
        help_text="Whether the user has submitted or skipped 'Children Info' onboarding screen",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

