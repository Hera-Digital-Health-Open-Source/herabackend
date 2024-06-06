from django.contrib import admin

from otp_auth.models import SmsOtpChallenge


@admin.register(SmsOtpChallenge)
class SmsOtpChallengeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'secret', 'status', 'solved_at', 'expires_at')
