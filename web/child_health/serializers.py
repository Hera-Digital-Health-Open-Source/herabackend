from rest_framework.fields import CurrentUserDefault, HiddenField
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from child_health.models import Child, Pregnancy, Vaccine


class PregnancySerializer(ModelSerializer):
    user = HiddenField(
        default=CurrentUserDefault(),
    )

    class Meta:
        model = Pregnancy
        fields = [
            'id',
            'user',
            'declared_pregnancy_week',
            'declared_date_of_last_menstrual_period',
            'declared_number_of_prenatal_visits',
            'estimated_start_date',
            'estimated_delivery_date',
        ]
        read_only_fields = ['id', 'estimated_start_date', 'estimated_delivery_date']


class ChildSerializer(ModelSerializer):
    user = HiddenField(
        default=CurrentUserDefault(),
    )
    past_vaccinations = PrimaryKeyRelatedField(
        many=True,
        queryset=Vaccine.objects.filter(is_active=True),
    )

    class Meta:
        model = Child
        fields = [
            'id',
            'user',
            'name',
            'date_of_birth',
            'gender',
            'past_vaccinations',
        ]
        read_only_fields = ['id']


class VaccineSerializer(ModelSerializer):
    class Meta:
        model = Vaccine
        fields = [
            'id',
            'name',
        ]
        read_only_fields = ['id']
