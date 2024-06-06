from django.urls import path

from webhook_survey_responses import views

urlpatterns = [
    path('webhook_survey_responses/', views.SurveyResponsesWebhookAPIView.as_view()),
]