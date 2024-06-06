from rest_framework import serializers


class CheckRegistrationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=255)
    is_registered = serializers.BooleanField(read_only=True)
