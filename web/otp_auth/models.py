from django.db import models
from django.utils import timezone

from otp_auth.managers import SmsOtpChallengeManager


class SmsOtpChallenge(models.Model):
    objects = SmsOtpChallengeManager()

    phone_number = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    expires_at = models.DateTimeField(blank=True, null=True)
    solved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone_number', 'secret'])
        ]
        verbose_name = 'SMS OTP Challenge'
        verbose_name_plural = 'SMS OTP Challenges'

    def mark_as_solved(self):
        self.solved_at = timezone.now()

    # @property
    def status(self):
        if self.solved_at is not None:
            return "Solved"
        elif self.expires_at < timezone.now():
            return "Expired"
        else:
            return "Active"

    def __str__(self):
        return f'Challenge for {self.phone_number}'


class CheckRegistrationResult:
    def __init__(self, phone_number, is_registered):
        self.phone_number = phone_number
        self.is_registered = is_registered
