from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from child_health.models import Pregnancy
from user_profile.models import UserProfile
from surveys.models import Survey
from events.models import NotificationEvent

from custom_user.admin.child_inline import ChildInline
from django.shortcuts import redirect


class PregnancyInline(admin.TabularInline):
    model = Pregnancy
    extra = 0


class UserProfileInline(admin.TabularInline):
    model = UserProfile


class SurveyInline(admin.TabularInline):
    model = Survey
    extra = 0


class NotificationEventInline(admin.TabularInline):
    model = NotificationEvent
    extra = 0
    fields = ('event_key', 'title', 'message')
    readonly_fields = ('title', 'message',)

    def title(self, obj):
        if obj.id is None:
            return ''
        return obj.push_title

    def message(self, obj):
        if obj.id is None:
            return ''
        return obj.push_body


class CustomNotification(User):
    class Meta:
        proxy = True


class YearOfBirthFilter(admin.SimpleListFilter):
    parameter_name = 'birth_year'
    title = _('Year of Birth')
    template = 'admin/filter/admin_input_filter.html'

    def lookups(self, request, model_admin):
        return ((None, None),)

    def choices(self, changelist):
        query_params = changelist.get_filters_params()
        query_params.pop(self.parameter_name, None)
        all_choice = next(super().choices(changelist))
        all_choice['query_params'] = query_params
        yield all_choice

    def queryset(self, request, queryset):
        value = self.value()
        date_range = []
        if value:
            date_range = value.split('-')
        if value and len(date_range) == 1:
            return queryset.filter(userprofile__date_of_birth__year__icontains=value)\
                .order_by('username').distinct('username')
        elif len(date_range) == 2:
            return queryset.filter(userprofile__date_of_birth__year__range=date_range)\
                .order_by('username').distinct('username')


class YearOfChildBirthFilter(admin.SimpleListFilter):
    parameter_name = 'child_birth_year'
    title = _('Has at Least One Child Born in Year')
    template = 'admin/filter/admin_input_filter.html'

    def lookups(self, request, model_admin):
        return ((None, None),)

    def choices(self, changelist):
        query_params = changelist.get_filters_params()
        query_params.pop(self.parameter_name, None)
        all_choice = next(super().choices(changelist))
        all_choice['query_params'] = query_params
        yield all_choice

    def queryset(self, request, queryset):
        value = self.value()
        date_range = []
        if value:
            date_range = value.split('-')
        if value and len(date_range) == 1:
            return queryset.filter(child__date_of_birth__year__icontains=value)\
                .order_by('username').distinct('username')
        elif len(date_range) == 2:
            return queryset.filter(child__date_of_birth__year__range=map(int, date_range))\
                .order_by('username').distinct('username')


class HasPregnancyFilter(admin.SimpleListFilter):
    parameter_name = 'has_pregnancy'
    title = _('User Has Pregnancy?')

    def lookups(self, request, model_admin):
        return [('yes', _('Yes')), ('no', _('No')), ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(pregnancy__user__isnull=False).distinct()
        elif value == 'no':
            return queryset.filter(pregnancy__user__isnull=True).distinct()
        else:
            return queryset


class HasChildrenFilter(admin.SimpleListFilter):
    parameter_name = 'has_children'
    title = _('User Has Children?')

    def lookups(self, request, model_admin):
        return [('yes', _('Yes')), ('no', _('No')), ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(child__user__isnull=False).distinct()
        elif value == 'no':
            return queryset.filter(child__user__isnull=True).distinct()


class SurveyFilter(admin.SimpleListFilter):
    parameter_name = 'survey'
    title = _('Survey Answers')

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Answered Yes to ALL Surveys')),
            ('no', _('Answered No to ALL Surveys')),
            ('not', _('Did Not Answer Any Survey')),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'not':
            return queryset.filter(survey__response__isnull=True).distinct()
        elif value == 'yes' or value == 'no':
            return queryset.filter(survey__response__icontains=value).distinct()


class NotificationFilter(admin.SimpleListFilter):
    parameter_name = 'notification'
    title = _('Notifications')

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Read ALL Notifications')),
            ('no', _('Did Not Read Any Notifications')),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(notificationevent__read_at__isnull=False).distinct()
        elif value == 'no':
            return queryset.filter(notificationevent__read_at__isnull=True).distinct()


class NameFilter(admin.SimpleListFilter):
    parameter_name = 'user_name'
    title = _('Name')
    template = 'admin/filter/admin_input_filter.html'

    def lookups(self, request, model_admin):
        return ((None, None),)

    def choices(self, changelist):
        query_params = changelist.get_filters_params()
        query_params.pop(self.parameter_name, None)
        all_choice = next(super().choices(changelist))
        all_choice['query_params'] = query_params
        yield all_choice

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(userprofile__name__icontains=value)


class PhoneFilter(admin.SimpleListFilter):
    parameter_name = 'user_phone'
    title = _('Phone')
    template = 'admin/filter/admin_input_filter.html'

    def lookups(self, request, model_admin):
        return ((None, None),)

    def choices(self, changelist):
        query_params = changelist.get_filters_params()
        query_params.pop(self.parameter_name, None)
        all_choice = next(super().choices(changelist))
        all_choice['query_params'] = query_params
        yield all_choice

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(username__icontains=value)


class NumberOfChildrenFilter(admin.SimpleListFilter):
    parameter_name = 'no_of_children'
    title = _('Number of Children')
    template = 'admin/filter/admin_input_filter.html'

    def lookups(self, request, model_admin):
        return ((None, None),)

    def choices(self, changelist):
        query_params = changelist.get_filters_params()
        query_params.pop(self.parameter_name, None)
        all_choice = next(super().choices(changelist))
        all_choice['query_params'] = query_params
        yield all_choice

    def queryset(self, request, queryset):
        value = self.value()
        count_range = []
        if value:
            count_range = value.split('-')
        if value and len(count_range) == 1:
            return queryset.annotate(num_child=Count('child')).filter(num_child=int(value))
        elif len(count_range) == 2:
            return queryset.annotate(num_child=Count('child')).filter(num_child__range=map(int, count_range))


class CustomNotificationAdmin(UserAdmin):
    list_filter = (PhoneFilter, NameFilter, 'userprofile__gender',
                   YearOfBirthFilter, HasPregnancyFilter,
                   HasChildrenFilter, YearOfChildBirthFilter, NumberOfChildrenFilter,
                   SurveyFilter, NotificationFilter)
    list_display = ['username', 'name']

    inlines = [
        UserProfileInline,
        PregnancyInline,
        ChildInline,
        SurveyInline,
        NotificationEventInline,
    ]

    fieldsets = (
        (None, {'fields': ('username',)}),
    )

    search_fields = []
    actions = ["send_push_notification"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def name(self, obj):
        user_profile = UserProfile.objects.get(user=obj)
        if user_profile:
            return user_profile.name
        else:
            return ''

    @method_decorator(staff_member_required)
    def send_push_notification(self, request, queryset):
        def _extract_user_id(user):
            return user.username
        users = list(map(_extract_user_id, queryset))
        request.session['selected_notification_users'] = users
        return redirect('/admin/events/instantnotification/add/')

    send_push_notification.short_description = "Send Notification"


admin.site.register(CustomNotification, CustomNotificationAdmin)
