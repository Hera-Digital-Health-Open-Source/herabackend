from django.contrib import admin
from django.utils.html import format_html, format_html_join
from child_health.models import Child, Vaccine


class ChildInline(admin.TabularInline):
    model = Child
    extra = 0
    readonly_fields = ('all_vaccinations',)
    fields = ('name', 'date_of_birth', 'gender', 'all_vaccinations')

    def all_vaccinations(self, obj):
        vaccinations = self.vaccinations()

        def _checkbox_data(vaccination):
            checked = 'checked' if vaccination.name in list(map(lambda x: x.vaccine.name, obj.pastvaccination_set.all())) else ''
            return (checked, vaccination.name)

        vaccinations_html = format_html_join('\n', '<div><input type="checkbox" readonly onclick="return false" {} /> {}</div>', list(map(_checkbox_data, vaccinations)))
        return format_html('<div>{}</div>', vaccinations_html)

    def vaccinations(self):
        return Vaccine.objects.all()
