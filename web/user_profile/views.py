from django.contrib.auth.models import User
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from user_profile.models import OnboardingProgress, PhoneNumberChangeRequest, UserProfile
from user_profile.serializers import OnboardingProgressSerializer, PhoneNumberChangeRequestAttemptSolveSerializer, \
    PhoneNumberChangeRequestResendOtpSerializer, PhoneNumberChangeRequestSerializer, UserProfileSerializer, \
    UserSerializer
from user_profile.throttles import ChangePhoneNumberRequestResendOtpThrottle, ChangePhoneNumberRequestThrottle


class UserProfileViewSet(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.get_queryset().exists():
            serializer.instance = self.get_queryset()[0]
        serializer.save()


class PhoneNumberChangeRequestViewSet(ModelViewSet):
    queryset = PhoneNumberChangeRequest.objects.all()
    serializer_class = PhoneNumberChangeRequestSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChangePhoneNumberRequestThrottle]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        throttle_classes=[ChangePhoneNumberRequestResendOtpThrottle],
        serializer_class=PhoneNumberChangeRequestResendOtpSerializer,
    )
    def resend_otp(self, request, pk=None):
        change_request: PhoneNumberChangeRequest = self.get_object()
        change_request.send_otp_via_sms()
        return Response(status=200)

    @action(detail=True, methods=['post'], serializer_class=PhoneNumberChangeRequestAttemptSolveSerializer)
    def attempt_solve(self, request, pk=None):
        change_request: PhoneNumberChangeRequest = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        guess_secret = serializer.validated_data["guess_secret"]
        change_request.attempt_solve(guess_secret)
        return Response(status=200)


class UserViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=['get'], serializer_class=UserSerializer)
    def me(self, request):
        user = self.get_object()
        serializer = self.get_serializer(user, many=False)
        return Response(status=200, data=serializer.data)


class OnboardingProgressViewSet(ModelViewSet):
    queryset = OnboardingProgress.objects.all()
    serializer_class = OnboardingProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.get_queryset().exists():
            serializer.instance = self.get_queryset()[0]
        serializer.save()