from django.contrib.auth.models import User
from django.core import validators
from django.db import models
from django.utils.translation import gettext_lazy as _

from child_health.managers import PregnancyManager


AVERAGE_WEEKS_PER_MONTH = 4.34524


class Pregnancy(models.Model):
    objects = PregnancyManager()

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    declared_pregnancy_week = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=(
            validators.MinValueValidator(1),
            validators.MaxValueValidator(42),
        ),
    )
    declared_date_of_last_menstrual_period = models.DateField(blank=True, null=True)
    declared_number_of_prenatal_visits = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=(
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9),
        )
    )
    estimated_start_date = models.DateField()
    estimated_delivery_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Pregnancies'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['estimated_delivery_date']),
        ]


class Child(models.Model):
    class ChildGender(models.TextChoices):
        MALE = 'MALE', _('Male')
        FEMALE = 'FEMALE', _('Female')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=20,
        choices=ChildGender.choices,
    )
    past_vaccinations = models.ManyToManyField(
        'Vaccine',
        through='PastVaccination',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Children'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date_of_birth']),
        ]


class Vaccine(models.Model):
    name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=100, null=True, blank=True)
    applicable_for_male = models.BooleanField(default=True)
    applicable_for_female = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "" if self.is_active else "[Draft] "
        if self.nickname is None:
            description = self.name
        else:
            description = f"{self.name} :: {self.nickname}"
        return status + description

    def friendly_name(self) -> str:
        return self.nickname if self.nickname is not None else self.name


class VaccineDose(models.Model):
    vaccine = models.ForeignKey(
        Vaccine,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=50)
    week_age = models.PositiveSmallIntegerField()
    notes_for_parent = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_month_age(self):
        return round(self.week_age / AVERAGE_WEEKS_PER_MONTH)

    class Meta:
        indexes = [
            models.Index(fields=['week_age']),
            models.Index(fields=['vaccine']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_month_age()} months)"


class PastVaccination(models.Model):
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
    )
    vaccine = models.ForeignKey(
        Vaccine,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['child']),
            models.Index(fields=['vaccine']),
        ]
        unique_together = [
            ['child', 'vaccine',],
        ]
