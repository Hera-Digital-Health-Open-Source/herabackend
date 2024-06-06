from django.conf import settings
from rest_framework.serializers import ModelSerializer
from rest_framework.fields import ListField

from .models import HealthCenter


class HealthCentersSirializer(ModelSerializer):
    class Meta:
        model = HealthCenter
        fields = ("name", "address", "geolocation", "activity_state", "type", "last_updated")
