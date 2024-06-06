from rest_framework import routers

from user_profile.views import OnboardingProgressViewSet, PhoneNumberChangeRequestViewSet, UserProfileViewSet, UserViewSet


router = routers.SimpleRouter()
router.register('user_profiles', UserProfileViewSet, basename='user_profile')
router.register('users', UserViewSet, basename='user')
router.register('phone_number_change_requests', PhoneNumberChangeRequestViewSet,
                basename='phone_number_change_requests')
router.register('onboarding_progresses', OnboardingProgressViewSet, basename='user')

urlpatterns = router.urls
