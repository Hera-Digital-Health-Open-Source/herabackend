from django.db import models
from django_google_maps.fields import AddressField, GeoLocationField


class HealthCenter(models.Model):
    name = models.CharField(max_length=255)
    address = AddressField(max_length=200)
    geolocation = GeoLocationField(blank=True)
    activity_state = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    is_disaster = models.BooleanField(default=False)
    sa_id = models.IntegerField(null=True, blank=True)

