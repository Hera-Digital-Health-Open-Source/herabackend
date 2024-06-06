from django.urls import path

from infra import views


urlpatterns = [
    path('health_check/', views.HealthCheckView.as_view()),
]
