from typing import Optional

import phonenumbers
from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import CurrentUserDefault, HiddenField, ModelSerializer, Serializer

from hera.settings import HERA_OTP_LENGTH
from user_profile.models import OnboardingProgress, PhoneNumberChangeRequest, UserProfile


class UserProfileSerializer(ModelSerializer):
    user = HiddenField(
        default=CurrentUserDefault(),
    )

    class Meta:
        model = UserProfile
        fields = ['user', 'name', 'gender', 'date_of_birth', 'agree_to_terms_at', 'language_code', 'timezone']


class PhoneNumberChangeRequestSerializer(ModelSerializer):
    user = HiddenField(
        default=CurrentUserDefault(),
    )

    class Meta:
        model = PhoneNumberChangeRequest
        fields = ['id', 'user', 'new_phone_number', 'expires_at']
        read_only_fields = ['id', 'user', 'expires_at']


class PhoneNumberChangeRequestResendOtpSerializer(Serializer):
    pass


class PhoneNumberChangeRequestAttemptSolveSerializer(ModelSerializer):
    user = HiddenField(
        default=CurrentUserDefault(),
    )
    guess_secret = CharField(min_length=HERA_OTP_LENGTH, max_length=HERA_OTP_LENGTH)

    class Meta:
        model = PhoneNumberChangeRequest
        fields = ['id', 'user', 'new_phone_number', 'expires_at', 'guess_secret', 'solved_at']
        read_only_fields = ['id', 'user', 'new_phone_number', 'expires_at', 'solved_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Valid user 1',
            value={
                'id': 1,
                'is_staff': False,
                'phone_country_code': '65',
                'phone_national_number': '91234567',
                'phone_full_number': "+6591234567",
                'date_joined': '2021-12-02T14:11:12.911866Z',
            },
            response_only=True,
        )
    ],
)


class UserSerializer(ModelSerializer):
    phone_country_code = SerializerMethodField()
    phone_national_number = SerializerMethodField()
    phone_full_number = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'date_joined', 'is_staff',
            'phone_country_code', 'phone_national_number', 'phone_full_number',
        ]

    def get_phone_country_code(self, obj: User) -> Optional[str]:
        try:
            parsed_phone_number = phonenumbers.parse(obj.username)
            return str(parsed_phone_number.country_code)
        except phonenumbers.phonenumberutil.NumberParseException:
            return None

    def get_phone_national_number(self, obj: User) -> Optional[str]:
        try:
            parsed_phone_number = phonenumbers.parse(obj.username)
            return str(parsed_phone_number.national_number)
        except phonenumbers.phonenumberutil.NumberParseException:
            return None

    def get_phone_full_number(self, obj: User) -> Optional[str]:
        try:
            _ = phonenumbers.parse(obj.username)
            return obj.username
        except phonenumbers.phonenumberutil.NumberParseException:
            return None


class OnboardingProgressSerializer(ModelSerializer):
    user = HiddenField(
        default=CurrentUserDefault(),
    )

    class Meta:
        model = OnboardingProgress
        fields = [
            'user',
            'has_filled_profile',
            'has_filled_pregnancy_status',
            'has_filled_children_info',
        ]
