from abc import ABC

from rest_framework.fields import CharField, DateField
from rest_framework.serializers import Serializer, ModelSerializer
from events.models import NotificationEvent


class CalendarEventSerializer(Serializer):
    date = DateField()
    event_type = CharField()


class NotificationEventSerializer(ModelSerializer):
    date = DateField()
    destination = CharField()
    
    class Meta:
        model = NotificationEvent
        fields = [
            'id',
            'notification_type',
            'destination',
            'date',
            'push_title',
            'push_body',
            'in_app_content',
            'read_at',
            'created_at',
        ]