from django.contrib import admin
from django.urls import URLPattern, path, include

from .views import HealthCenters_list

urlpatterns = [
    path('/', include(HealthCenters_list)),
]
