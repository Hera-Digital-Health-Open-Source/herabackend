from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from hera.settings import HERA_OTP_LENGTH
from otp_auth.utils import generate_secret, sanitize_phone_number


if TYPE_CHECKING:
    from otp_auth.models import SmsOtpChallenge


class SmsOtpChallengeManager(models.Manager):
    def make_challenge(self, phone_number: str) -> SmsOtpChallenge:
        clean_phone_number = sanitize_phone_number(phone_number)
        if clean_phone_number == "+16507357357":  # tester number
            secret = "735735"
        else:
            secret = generate_secret(HERA_OTP_LENGTH)
        expires_at = timezone.now() + timedelta(minutes=10)
        return self.create(
            phone_number=clean_phone_number,
            secret=secret,
            expires_at=expires_at,
        )
