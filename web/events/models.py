import pytz

from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField, HStoreField
from django.contrib.postgres.indexes import HashIndex
from django.core.validators import MinLengthValidator, MinValueValidator, RegexValidator
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from functools import lru_cache
from liquid import Template

from events.constants import CalendarEventType


class LanguageCode(models.TextChoices):
    ENGLISH = 'en', _('English')
    TURKISH = 'tr', _('Turkish')
    ARABIC = 'ar', _('Arabic')
    PASHTO = 'ps', _('Pashto')
    DARI = 'prs', _('Dari')


class NotificationType(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            MinLengthValidator(10),
            RegexValidator(
                r' ',
                _('No spaces allowed'),
                inverse_match=True,
            ),
            RegexValidator(
                r'[A-Z]',
                _('No UPPERCASE allowed'),
                inverse_match=True,
            ),
            RegexValidator(
                r'^[a-z0-9._]+$',
                _('Only lowercase character, number, . and _ allowed'),
            ),
        ],
        help_text="Alphanumeric code you can send to the devs to let them trigger this notification on certain "
                  "condition."
    )
    description = models.CharField(
        max_length=1000,
        help_text="When is this notification sent? What is the purpose of this notification? Note for translators & "
                  "devs?",
    )

    def __str__(self):
        return f"{self.code}"


class NotificationTemplateVariable(models.Model):
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=50,
        help_text="The name of the variable. Can be used in template, e.g. {{ variable_name }}.",
        validators=[
            RegexValidator(
                r' ',
                _('No spaces allowed'),
                inverse_match=True,
            ),
            RegexValidator(
                r'[A-Z]',
                _('No UPPERCASE allowed'),
                inverse_match=True,
            ),
            RegexValidator(
                r'^[a-z0-9._]+$',
                _('Only lowercase character, number, . and _ allowed'),
            ),
        ],
    )
    example_values = ArrayField(
        models.CharField(
            max_length=255,
        ),
        help_text="Some example values of this variable",
    )
    description = models.CharField(
        max_length=1000,
        help_text="What does this variable mean?",
        blank=False,
        null=False,
    )

    def __str__(self):
        return f"{self.notification_type.code} => {self.name}"


class NotificationTemplate(models.Model):
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    language_code = models.CharField(
        max_length=5,
        choices=LanguageCode.choices,
    )
    push_title = models.CharField(
        max_length=100,
        help_text="Title to be shown in push notification (shown in Android / iOS notification centre and lock screen)",
    )
    push_body = models.CharField(
        max_length=255,
        help_text="Body to be shown in push notification (shown in Android / iOS notification centre and lock screen)",
    )
    in_app_content = models.CharField(
        max_length=1000,
        help_text="Text to be shown inside HERA app notification screen.",
    )
    twilio_content_sid = models.CharField(
        max_length=255,
        help_text="Whatsapp Template SID in Twilio Content editor",
        null=True
    )

    class Meta:
        unique_together = [
            ['notification_type', 'language_code'],
        ]

    def __str__(self):
        return f"NotificationTemplate for {self.notification_type_id} ({self.language_code.upper()})"

    @property
    @lru_cache(maxsize=1)
    def push_title_template(self):
        return Template(self.push_title)

    @property
    @lru_cache(maxsize=1)
    def push_body_template(self):
        return Template(self.push_body)

    @property
    @lru_cache(maxsize=1)
    def in_app_content_template(self):
        return Template(self.in_app_content)

    def rendered_push_title(self, context: dict):
        return self.push_title_template.render(context)

    def rendered_push_body(self, context: dict):
        return self.push_body_template.render(context)

    def rendered_in_app_content(self, context: dict):
        return self.in_app_content_template.render(context)


class NotificationSchedule(models.Model):
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.PROTECT,
    )
    calendar_event_type = models.CharField(
        max_length=50,
        choices=CalendarEventType.choices,
    )
    offset_days = models.SmallIntegerField()
    time_of_day = models.TimeField()
    push_time_to_live = models.DurationField(
        "Duration until notification expires",
        default=timedelta(days=1),
        help_text="(days hh:mm:ss) If this amount of time has passed after the calendar event, no notification will be generated.",
        validators=[
            MinValueValidator(timedelta(minutes=5)),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ['calendar_event_type', 'offset_days', 'time_of_day',],
        ]

    def __str__(self):
        if self.offset_days < 0:
            abs_offset = self.offset_days * -1
            return f"{abs_offset} day before {self.calendar_event_type} at {self.time_of_day} using {self.notification_type} template"
        elif self.offset_days > 0:
            return f"{self.offset_days} day after {self.calendar_event_type} at {self.time_of_day} using {self.notification_type} template"
        else:
            return f"On the day of {self.calendar_event_type} at {self.time_of_day} using {self.notification_type} template"

    def get_notification_window(self, calendar_event_date: date, user_timezone) -> (datetime, datetime):
        notification_date = calendar_event_date + timedelta(days=self.offset_days)
        notification_available_at = user_timezone.localize(datetime.combine(notification_date, self.time_of_day))
        notification_expires_at = notification_available_at + self.push_time_to_live
        return (notification_available_at, notification_expires_at,)

class InstantNotification(models.Model):
    phone_numbers = ArrayField(
        models.CharField(max_length=15, blank=False),
    )
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class NotificationEvent(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    event_key = models.CharField(
        null=True,
        blank=True,
        max_length=100,
    )
    schedule = models.ForeignKey(
        NotificationSchedule,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    context = HStoreField(default=dict)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    notification_available_at = models.DateTimeField()
    notification_expires_at = models.DateTimeField()
    push_notification_sent_at = models.DateTimeField(blank=True, null=True, default=None)
    read_at = models.DateTimeField(blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ['event_key', 'schedule'],
        ]
        index_together = [
            ['user']
        ]

    @property
    @lru_cache(maxsize=1)
    def language_code(self):
        try:
            return self.user.userprofile.language_code
        except User.userprofile.RelatedObjectDoesNotExist:
            return settings.LANGUAGE_CODE

    @property
    @lru_cache(maxsize=1)
    def template(self):
        template = self.notification_type.notificationtemplate_set.filter(language_code__startswith=self.language_code).first()
        if template is None:  # fallback to English
            template = self.notification_type.notificationtemplate_set.filter(language_code__startswith='en').first()
        return template

    @property
    @lru_cache(maxsize=1)
    def push_title(self):
        return self.template.rendered_push_title(self.context)

    @property
    @lru_cache(maxsize=1)
    def push_body(self):
        return self.template.rendered_push_body(self.context)

    @property
    @lru_cache(maxsize=1)
    def in_app_content(self):
        return self.template.rendered_in_app_content(self.context)
    
    @property
    @lru_cache(maxsize=1)
    def twilio_content_sid(self):
        if self.template is not None:
            return self.template.twilio_content_sid

    @property
    def destination(self):
        """ The screen in the front-end that should be opened
        when user taps on this notification
        """
        return 'calendar'

    @property
    def date(self):
        if 'date' in self.context:
            return self.context['date']
        else:
            return None
