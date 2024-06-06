"""hera URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from two_factor.urls import urlpatterns as tf_urls
from health_center import views as health_center_views



urlpatterns = [
    path('', include(tf_urls)),
    path('admin/', admin.site.urls),
    path('otp_auth/', include('otp_auth.urls')),
    path('', include('user_profile.urls')),
    path('', include('child_health.urls')),
    path('', include('events.urls')),
    path('', include('surveys.urls')),
    path('', include('whatsapp_opt_history.urls')),
    path('', include('hotline_ai_chatbot.urls')),
    path('', include('webhook_survey_responses.urls')),
    path('', include('data_dashboard.urls')),
    path('infra/', include('infra.urls')),
    path('browse_api_auth', include('rest_framework.urls', namespace='rest_framework')),
    path('api_docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api_docs/redoc/', SpectacularRedocView.as_view(), name='redoc'),
    path('health_centers/', health_center_views.health_centers_list),
    path('translation_glossary/', include('translation_glossary.urls')),
    path('text_to_speech/', include('text_to_speech.urls')),
    path('', include('concepts.urls'))
]
