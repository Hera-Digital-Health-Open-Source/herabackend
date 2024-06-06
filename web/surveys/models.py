from datetime import date, datetime, timedelta
from functools import lru_cache

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import HStoreField
from django.core.validators import MinLengthValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models.deletion import CASCADE
from django.utils.translation import gettext_lazy as _
from liquid import Template

from events.constants import CalendarEventType


class LanguageCode(models.TextChoices):
    ENGLISH = 'en', _('English')
    TURKISH = 'tr', _('Turkish')
    ARABIC = 'ar', _('Arabic')
    PASHTO = 'ps', _('Pashto')
    DARI = 'prs', _('Dari')


class SurveyType(models.TextChoices):
    MULTIPLE_CHOICE = 'MULTIPLE_CHOICE', _('Multiple Choice')
    TEXT = 'TEXT', _('Text')


class SurveyTemplate(models.Model):
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
        help_text="Alphanumeric code you can send to the devs to let them trigger this survey on certain condition.",
    )
    description = models.CharField(
        max_length=1000,
        help_text="When is this survey sent? What is the purpose of this survey? Note for translators & devs?",
    )
    survey_type = models.CharField(choices=SurveyType.choices, max_length=255)

    def __str__(self):
        return f"{self.code}"


class SurveyTemplateOption(models.Model):
    survey_template = models.ForeignKey(SurveyTemplate, on_delete=models.CASCADE)
    code = models.CharField(
        max_length=20,
        unique=True,
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
    option_en = models.CharField(
        "Option in English",
        max_length=50,
    )
    option_tr = models.CharField(
        "Option in Turkish",
        max_length=50,
        blank=True,
        null=True,
    )
    option_ar = models.CharField(
        "Option in Arabic",
        max_length=50,
        blank=True,
        null=True,
    )
    option_ps = models.CharField(
        "Option in Pashto",
        max_length=50,
        blank=True,
        null=True,
    )
    option_ars = models.CharField(
        "Option in Dari",
        max_length=50,
        blank=True,
        null=True,
    )


class SurveyTemplateTranslation(models.Model):
    survey_template = models.ForeignKey(SurveyTemplate, on_delete=models.CASCADE)
    language_code = models.CharField(
        max_length=5,
        choices=LanguageCode.choices,
    )
    question = models.CharField(
        max_length=255,
        help_text="Question to be shown in the survey pop-up in app",
    )
    twilio_content_sid = models.CharField(
        max_length=255,
        help_text="Whatsapp Template SID in Twilio Content editor",
        null=True
    )

    class Meta:
        unique_together = [
            ['survey_template', 'language_code'],
        ]

    def __str__(self):
        return f"SurveyTemplateTranslation for {self.survey_template.id} ({self.language_code.upper()})"

    @property
    def question_template(self):
        return Template(self.question)

    def rendered_question(self, context: dict):
        return self.question_template.render(context)


class SurveySchedule(models.Model):
    survey_template = models.ForeignKey(SurveyTemplate, on_delete=models.CASCADE)
    calendar_event_type = models.CharField(
        max_length=50,
        choices=CalendarEventType.choices,
    )
    offset_days = models.SmallIntegerField()
    time_of_day = models.TimeField()
    time_to_live = models.DurationField(
        "Duration until survey expires",
        default=timedelta(days=7),
        help_text="(days hh:mm:ss) If this amount of time has passed after the calendar event, no survey will be generated.",
        validators=[
            MinValueValidator(timedelta(hours=1)),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.offset_days < 0:
            abs_offset = self.offset_days * -1
            return f"{abs_offset} day before {self.calendar_event_type} at {self.time_of_day} using {self.survey_template} template"
        elif self.offset_days > 0:
            return f"{self.offset_days} day after {self.calendar_event_type} at {self.time_of_day} using {self.survey_template} template"
        else:
            return f"On the day of {self.calendar_event_type} at {self.time_of_day} using {self.survey_template} template"

    def get_survey_window(self, calendar_event_date: date, user_timezone) -> (datetime, datetime):
        survey_date = calendar_event_date + timedelta(days=self.offset_days)
        survey_available_at = user_timezone.localize(datetime.combine(survey_date, self.time_of_day))
        survey_expires_at = survey_available_at + self.time_to_live
        return (survey_available_at, survey_expires_at,)


class Survey(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE)
    event_key = models.CharField(
        null=True,
        blank=True,
        max_length=100,
    )
    schedule = models.ForeignKey(
        SurveySchedule,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    survey_template = models.ForeignKey(SurveyTemplate, on_delete=CASCADE)
    context = HStoreField(default=dict)
    response = models.CharField(max_length=255, blank=True, null=True)
    available_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    is_served = False # to mark an instance as "served", to prevent it to be served again.
    
    class Meta:
        unique_together = [
            ['event_key', 'schedule'],
        ]
        index_together = [
            ['user', 'response'],
        ]

    @property
    def survey_type(self):
        return self.survey_template.survey_type

    @property
    @lru_cache(maxsize=1)
    def language_code(self):
        try:
            return self.user.userprofile.language_code
        except User.userprofile.RelatedObjectDoesNotExist:
            return settings.LANGUAGE_CODE

    @property
    @lru_cache(maxsize=1)
    def survey_template_translation(self) -> SurveyTemplateTranslation:
        return self.survey_template.surveytemplatetranslation_set.filter(
            language_code__startswith=self.language_code).first()

    @property
    @lru_cache(maxsize=1)
    def question(self):
        if self.survey_template_translation is not None:
            return self.survey_template_translation.rendered_question(self.context)

    @property
    @lru_cache(maxsize=1)
    def twilio_content_sid(self):
        if self.survey_template_translation is not None:
            return self.survey_template_translation.twilio_content_sid
