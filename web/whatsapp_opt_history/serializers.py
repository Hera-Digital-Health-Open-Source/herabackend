from django.contrib.auth.models import User

from rest_framework import serializers
from whatsapp_opt_history.models import WhatsAppOptHistory

class WhatsAppOptInOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppOptHistory
        fields = [
            'username',
            'opt_status',
            'opt_datetime',
            'source'
        ]


    def validate(self, data):
        username = data.get('username')
        matched_user = User.objects.filter(username=username).first()
        if matched_user is None:
            raise serializers.ValidationError("User with this username does not exist.")

        return data

    def create(self, validated_data):
        # Ignore any value provided by the user for opt_datetime
        validated_data.pop('opt_datetime', None)
        return super().create(validated_data)
