from django_filters.rest_framework import FilterSet, DateFilter

from child_health.models import Pregnancy, Vaccine


class PregnancyFilter(FilterSet):
    min_delivery_date = DateFilter(field_name='estimated_delivery_date', lookup_expr='gte')
    max_delivery_date = DateFilter(field_name='estimated_delivery_date', lookup_expr='lte')

    class Meta:
        model = Pregnancy
        fields = ('min_delivery_date', 'max_delivery_date',)
