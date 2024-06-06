from django.contrib import admin
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from events.forms import NotificationTemplateForm, NotificationTemplateVariableForm
from events.models import NotificationEvent, NotificationTemplate, NotificationTemplateVariable, NotificationType, NotificationSchedule, InstantNotification


class NotificationTemplateVariableInline(admin.TabularInline):
    model = NotificationTemplateVariable
    form = NotificationTemplateVariableForm
    extra = 1


class NotificationTemplateInline(admin.TabularInline):
    model = NotificationTemplate
    form = NotificationTemplateForm
    max_num = 5


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ('code', 'description',)
    search_fields = ('code', 'description',)
    ordering = ('code',)
    inlines = [
        NotificationTemplateVariableInline,
        NotificationTemplateInline,
    ]


@admin.register(NotificationSchedule)
class NotificationScheduleAdmin(admin.ModelAdmin):
    ordering = ('calendar_event_type', 'offset_days', 'time_of_day',)


@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    pass


@admin.register(InstantNotification)
class InstantNotificationAdmin(admin.ModelAdmin):
    search_fields = ('notification_type',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(InstantNotificationAdmin, self).get_form(request, obj, **kwargs)
        # get_form is called twice. Need this to skip unnecessary session pop
        if 'fields' in kwargs and kwargs['fields'] is None:
            return form

        if 'phone_numbers' in form.base_fields:
            users = request.session.pop('selected_notification_users', [])
            if len(users):
                form.base_fields['phone_numbers'].initial = users
        return form

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
