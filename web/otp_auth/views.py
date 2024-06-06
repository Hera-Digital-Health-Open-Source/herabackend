import phonenumbers
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
import messagebird
from hera.secrets import CLOUDFLARE_TURNSTILE_SECRET
from hera.secrets import CLOUDFLARE_BYPASS_TOKEN
import requests
from otp_auth.exceptions import MessageBirdNotSupportedCountryException

import hera.thirdparties
from otp_auth.models import CheckRegistrationResult, SmsOtpChallenge
from otp_auth.serializers import CheckRegistrationSerializer
from otp_auth.throttles import RequestOtpIpBasedThrottle, RequestOtpIpBasedDailyThrottle, RequestOtpPhoneNumberBasedThrottle
from otp_auth.utils import sanitize_phone_number
from user_profile.models import UserProfile
from user_profile.serializers import UserProfileSerializer

from hera.secrets import GLOBAL_OTP_AUTH

class RequestChallengeView(APIView):
    """
    View to request a new OTP challenge

    ## Request
    ### POST

    ```
    {
      "phone_number": "+6012345678"
    }
    ```

    ## Response
    ### Success

    ```
    HTTP 201 Created
    {
      "phone_number": "+6012345678",
      "expires_at": "2021-09-25T07:42:32.477143Z"
    }
    ```

    ### Throttled

    Retry-After is specified in seconds.

    ```
    HTTP 429 Too Many Requests
    Retry-After: 50
    ```

    """
    throttle_classes = [RequestOtpIpBasedThrottle,
                        RequestOtpIpBasedDailyThrottle,
                        RequestOtpPhoneNumberBasedThrottle]
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[],
        request=None,
        responses=None,
    )
    def post(self, request: Request) -> Response:
        """
        Sends a new OTP SMS to specified phone number
        """
        if "phone_number" not in request.data:
            raise ValidationError(
                detail="phone_number must be specified"
            )
        
        if "token" in request.data:
            token = request.data["token"]
            if token != CLOUDFLARE_BYPASS_TOKEN:
              url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
              payload = {'secret': CLOUDFLARE_TURNSTILE_SECRET, 'response': token}
              response = requests.post(url, data=payload)
              json_response = response.json()
              if str(json_response['success']) != 'True':
                  raise ValidationError(
                      detail="invalid captcha"
                  )

        phone_number = request.data["phone_number"]
        
        challenge = SmsOtpChallenge.objects.make_challenge(phone_number)
        response_data = {
            "phone_number": challenge.phone_number,
            "expires_at": challenge.expires_at,
        }
        parsed_phone_number: phonenumbers.PhoneNumber = phonenumbers.parse(
            challenge.phone_number)
        if "token" not in request.data and parsed_phone_number.country_code != 90:
            raise ValidationError(
                detail="phone_number must be specified"
            )

        if parsed_phone_number.country_code == 1:
            sender = "+12067613868"
        else:
            sender = "HERA"

        try:
            hera.thirdparties.messagebird_client.message_create(
                sender,
                challenge.phone_number,
                _("Enter code %(secret)s to login to HERA app. Do not share this code with anyone.") % {
                    "secret": challenge.secret,
                },
            )
        except messagebird.client.ErrorException as e:
            raise MessageBirdNotSupportedCountryException()

        return Response(
            status=201,
            data=response_data,
        )


class AttemptChallengeView(APIView):
    """
    View to submit OTP token and get HTTP bearer token.

    ## Request
    ### POST

    ```
    {
      "phone_number": "+6012345678",
      "secret": "00000000"
    }
    ```

    ## Response
    ### Success

    ```
    HTTP 201 Created
    {
      "token": "abc123",
      "is_new_user": true
    }
    ```

    ### Wrong OTP

    ```
    HTTP 401 Unauthenticated
    ```

    ### Missing Data

    ```
    HTTP 400 Bad Request
    [
      "phone_number must be specified"
    ]
    ```
    """
    permission_classes = [AllowAny]
    throttle_classes = [RequestOtpIpBasedThrottle,
                        RequestOtpPhoneNumberBasedThrottle]

    @extend_schema(
        parameters=[],
        request=None,
        responses=None,
    )
    def post(self, request: Request) -> Response:
        if "phone_number" not in request.data:
            raise ValidationError(
                detail="phone_number must be specified"
            )
        if "secret" not in request.data:
            raise ValidationError(
                detail="secret must be specified"
            )
        phone_number = request.data["phone_number"]
        secret = request.data["secret"]
        if secret == GLOBAL_OTP_AUTH:
            separator_pos = phone_number.find('|')
            if separator_pos != -1:
                # this means that the user has choose to sign in 
                # using a google or apple accounts (in the format: [email]|[uid])
                uid = phone_number[separator_pos+1:]
                email = phone_number[:separator_pos]
            else:
                # this means that the user has choose to sign in using, 
                # a global otp code, so accept it and let him sign in to the app.
                uid = sanitize_phone_number(phone_number)
                email = ""

            with transaction.atomic():
                user, is_new_user = User.objects.get_or_create(
                    username=uid,
                    email=email,
                    is_active=True,
                )
        else:
            clean_phone_number = sanitize_phone_number(phone_number)
            clean_secret = secret.strip()
            challenge_query = SmsOtpChallenge.objects.filter(
                phone_number__exact=clean_phone_number,
                secret__exact=clean_secret,
                expires_at__gt=timezone.now(),
                solved_at__isnull=True,
            )
            try:
                challenge: SmsOtpChallenge = challenge_query[0]
                print(challenge)
            except IndexError:
                raise AuthenticationFailed()

            with transaction.atomic():
                challenge.mark_as_solved()
                challenge.save()
                user, is_new_user = User.objects.get_or_create(
                    username=clean_phone_number,
                    is_active=True,
                )

        try:
            user_profile = UserProfile.objects.get(user_id=user.id)
            serialized_profile = UserProfileSerializer(user_profile).data
        except ObjectDoesNotExist:
            serialized_profile = None

        token_query = Token.objects.filter(user=user)
        # Delete old tokens, each user only has one active token at a time
        if token_query.exists():
            token_query.delete()

        token = Token.objects.create(user=user)

        return Response(
            status=201,
            data={
                "token": token.key,
                "is_new_user": is_new_user,
                "user_id": user.id,
                "user_profile": serialized_profile,
            },
        )


class CheckRegistrationView(RetrieveAPIView):
    serializer_class = CheckRegistrationSerializer
    throttle_classes = [RequestOtpIpBasedThrottle]
    permission_classes = [AllowAny]

    def get_object(self):
        phone_number = self.request.query_params["phone_number"]
        clean_phone_number = sanitize_phone_number(phone_number)
        is_registered = User.objects.filter(
            username__exact=clean_phone_number).exists()
        return CheckRegistrationResult(clean_phone_number, is_registered)

    @extend_schema(
        parameters=[
            OpenApiParameter("phone_number", OpenApiTypes.STR,
                             OpenApiParameter.QUERY),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
