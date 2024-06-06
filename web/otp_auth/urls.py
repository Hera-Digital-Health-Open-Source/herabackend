from django.urls import path

from otp_auth import views


urlpatterns = [
    path('request_challenge/', views.RequestChallengeView.as_view()),
    path('attempt_challenge/', views.AttemptChallengeView.as_view()),
    path('check_registration/', views.CheckRegistrationView.as_view()),
]
