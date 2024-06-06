from django.contrib import admin

from child_health.models import Vaccine, VaccineDose, Child, Pregnancy, PastVaccination


class VaccineDoseInline(admin.TabularInline):
    model = VaccineDose


@admin.register(Vaccine)
class VaccineAdmin(admin.ModelAdmin):
    inlines = [
        VaccineDoseInline,
    ]
    actions = ['activate', 'deactivate']
    list_filter = ['is_active']

    @admin.action(description='Activate selected vaccines')
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate selected vaccines (back to draft)')
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


class PastVaccinationInline(admin.TabularInline):
    model = PastVaccination
    extra = 0


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'gender']
    inlines = [PastVaccinationInline]


@admin.register(Pregnancy)
class PregnancyAdmin(admin.ModelAdmin):
    list_display = ['user']


@admin.register(PastVaccination)
class PastVaccinationAdmin(admin.ModelAdmin):
    list_display = ['child_name', 'vaccine']

    def child_name(self, obj):
        return obj.child.name
