import json
from django.contrib import admin
from django_google_maps import fields as map_fields
from django_google_maps import widgets as map_widgets
from .models import HealthCenter


class HealthCentersAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'geolocation')
    formfield_overrides = {
        map_fields.AddressField: {
            'widget': map_widgets.GoogleMapsAddressWidget(attrs={
                'data-autocomplete-options':
                json.dumps({'types': ['geocode', 'establishment'], })
            })
        },

    }


admin.site.register(HealthCenter, HealthCentersAdmin)
