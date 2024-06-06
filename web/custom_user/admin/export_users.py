import functools
import numpy as np
from django.contrib.auth.models import User
from child_health.models import Pregnancy, Child
from user_profile.models import UserProfile
from ..utils import verbose_name
from datetime import datetime, timedelta
from django.db.models import Count

USER_ATTRIBUTES = ['username', 'date_joined', 'email']
USER_PROFILE_ATTRIBUTES = ['name', 'gender', 'date_of_birth', 'agree_to_terms_at', 'language_code', 'timezone']
PREGNANCY_ATTRIBUTES = ['declared_pregnancy_week', 'declared_date_of_last_menstrual_period', 'declared_number_of_prenatal_visits', 'estimated_start_date', 'estimated_delivery_date']
CHILD_ATTRIBUTES = ['name', 'date_of_birth', 'gender', 'vaccinations']
SURVEY_RESPONSE_ATTRIBUTES = ['question', 'response']
NOTIFICATION_EVENT_ATTRIBUTES = ['title', 'message']
RESEARCHER_GROUP = 'Researcher'


def users_to_array(request, users):
    def _user_to_row(user):
        if request.user.groups.filter(name=RESEARCHER_GROUP).exists():
            username = user.username[:4] + 'XXXXXXX'
        else:
            username = user.username
        return [username, user.date_joined, user.email]
    return list(map(_user_to_row, users))


def get_attributes(obj, attrs):
    def _get_attr(attr):
        value = getattr(obj, attr)
        return value if value is None else str(value)
    return list(map(_get_attr, attrs))


def get_child_attributes(obj, attrs):
    def _get_attr(attr):
        if attr == 'vaccinations':
            return ', '.join(sorted(list(map(lambda x: x.vaccine.name, obj.pastvaccination_set.all()))))
        else:
            value = getattr(obj, attr)
            return value if value is None else str(value)
    return list(map(_get_attr, attrs))


def users_to_user_profiles_array(request, users):
    def _user_to_row(user):
        if hasattr(user, 'userprofile'):
            attributes = get_attributes(user.userprofile, USER_PROFILE_ATTRIBUTES)
            if request.user.groups.filter(name=RESEARCHER_GROUP).exists():
                attributes[0] = 'XXXXXXX'
            return attributes
        return [None for i in range(len(USER_PROFILE_ATTRIBUTES))]
    return list(map(_user_to_row, users))


def pregnancies_to_array(pregnancies):
    def _pregnancy_to_row(pregnancy):
        if pregnancy:
            return get_attributes(pregnancy, PREGNANCY_ATTRIBUTES)
        return [None for i in range(len(PREGNANCY_ATTRIBUTES))]
    return list(map(_pregnancy_to_row, pregnancies))


# @return 3D list. user > pregancy > attribute
def users_to_pregnancies_array(users, max_pregnancies):
    def _user_to_pregnancies_array(user):
        pregnancy_count = user.pregnancy_set.count()
        filled_pregnancies = list(user.pregnancy_set.all()) + [None for i in range(max_pregnancies - pregnancy_count)]
        return pregnancies_to_array(filled_pregnancies)

    pregnancies = list(map(_user_to_pregnancies_array, users))
    return np.reshape(pregnancies, (len(users), max_pregnancies * len(PREGNANCY_ATTRIBUTES)))


def children_to_array(request, children):
    def _child_to_row(child):
        if child:
            children_array = get_child_attributes(child, CHILD_ATTRIBUTES)
            if request.user.groups.filter(name=RESEARCHER_GROUP).exists():
                children_array[0] = 'XXXXXXX'
            return children_array
        return [None for i in range(len(CHILD_ATTRIBUTES))]
    return list(map(_child_to_row, children))


def users_to_children_array(request, users, max_children):
    def _user_to_children_array(user):
        children_count = user.child_set.count()
        filled_children = list(user.child_set.all()) + [None for i in range(max_children - children_count)]
        return children_to_array(request, filled_children)

    children = list(map(_user_to_children_array, users))
    return np.reshape(children, (len(users), max_children * len(CHILD_ATTRIBUTES)))


def survey_responses_to_array(surveys):
    def _survey_to_row(survey):
        if survey:
            return [survey.question, survey.response]
        return [None for i in range(len(SURVEY_RESPONSE_ATTRIBUTES))]
    return list(map(_survey_to_row, surveys))


def users_to_survey_responses_array(users, max_survey):
    def _user_to_survey_response_array(user):
        survey_count = user.survey_set.filter(response__isnull=False).count()
        surveys = list(user.survey_set.filter(response__isnull=False).all().order_by('-response')) + [None for i in range(max_survey - survey_count)]
        return survey_responses_to_array(surveys)
    responses = list(map(_user_to_survey_response_array, users))
    return np.reshape(responses, (len(users), max_survey * len(SURVEY_RESPONSE_ATTRIBUTES)))


def notifications_to_array(notifications):
    def _notification_to_row(notification):
        if notification and notification.template:
            return [notification.push_title, notification.push_body]
        return [None for i in range(len(NOTIFICATION_EVENT_ATTRIBUTES))]
    return list(map(_notification_to_row, notifications))


def users_to_notifications_array(users, max_notifications):
    def _user_to_notifications_array(user):
        notification_count = user.notificationevent_set.count()
        filled_notifications = list(user.notificationevent_set.all()) + [None for i in range(max_notifications - notification_count)]
        return notifications_to_array(filled_notifications)
    notifications = list(map(_user_to_notifications_array, users))
    return np.reshape(notifications, (len(users), max_notifications * len(NOTIFICATION_EVENT_ATTRIBUTES)))


class ExportUser:
    def call(self, request, queryset):
        if (queryset is None):
            queryset = self.get_all_users()

            date_joined__range__gte = request.GET.get('date_joined__range__gte')
            if date_joined__range__gte:
                queryset = queryset.filter(date_joined__gte = datetime.strptime(date_joined__range__gte, "%d/%m/%Y"))
            
            date_joined__range__lte = request.GET.get('date_joined__range__lte')
            if date_joined__range__lte:
                queryset = queryset.filter(date_joined__lte = datetime.strptime(date_joined__range__lte, "%d/%m/%Y")+ timedelta(days=1) - timedelta(seconds=1))
            
            user_phone = request.GET.get('user_phone')
            if user_phone:
                queryset = queryset.filter(username__icontains = user_phone)
            
            user_name = request.GET.get('user_name')
            if user_name:
                queryset = queryset.filter(userprofile__name__icontains=user_name)
            
            userprofile__gender__exact = request.GET.get('userprofile__gender__exact')
            if userprofile__gender__exact:
                queryset = queryset.filter(userprofile__gender__exact=userprofile__gender__exact)       
            
            birth_year = request.GET.get('birth_year')
            if birth_year:
                date_range = []
                if birth_year:
                    date_range = birth_year.split('-')
                if birth_year and len(date_range) == 1:
                    queryset = queryset.filter(userprofile__date_of_birth__year__icontains=birth_year) \
                        .order_by('username').distinct('username')
                elif len(date_range) == 2:
                    queryset = queryset.filter(userprofile__date_of_birth__year__range=date_range) \
                        .order_by('username').distinct('username')
            
            has_pregnancy = request.GET.get('has_pregnancy')
            if has_pregnancy == 'yes':
                queryset = queryset.filter(pregnancy__user__isnull=False).distinct()
            elif has_pregnancy == 'no':
                queryset = queryset.filter(pregnancy__user__isnull=True).distinct()

            has_children = request.GET.get('has_children')
            if has_children == 'yes':
                queryset = queryset.filter(child__user__isnull=False).distinct()
            elif has_children == 'no':
                queryset = queryset.filter(child__user__isnull=True).distinct()

            child_birth_year = request.GET.get('child_birth_year')
            if child_birth_year:
                date_range = child_birth_year.split('-')
                if child_birth_year and len(date_range) == 1:
                    queryset = queryset.filter(child__date_of_birth__year__icontains=child_birth_year) \
                        .order_by('username').distinct('username')
                elif len(date_range) == 2:
                    queryset = queryset.filter(child__date_of_birth__year__range=map(int, date_range)) \
                        .order_by('username').distinct('username')
            
            no_of_children = request.GET.get('no_of_children')
            if no_of_children:
                count_range = no_of_children.split('-')
                if no_of_children and len(count_range) == 1:
                    queryset = queryset.annotate(num_child=Count('child')).filter(num_child=int(no_of_children))
                elif len(count_range) == 2:
                    queryset = queryset.annotate(num_child=Count('child')).filter(num_child__range=map(int, count_range))
            
            survey = request.GET.get('survey')
            if survey == 'not':
                queryset = queryset.filter(survey__response__isnull=True).distinct()
            elif survey == 'yes' or survey == 'no':
                queryset = queryset.filter(survey__response__icontains=survey).distinct()
            
            notification = request.GET.get('notification')
            if notification == 'yes':
                queryset = queryset.filter(notificationevent__read_at__isnull=False).distinct()
            elif notification == 'no':
                queryset = queryset.filter(notificationevent__read_at__isnull=True).distinct()

        users = queryset
        users_array = users_to_array(request, users)

        export_settings = request.GET.getlist('export_settings[]')

        user_profiles_array = []
        pregnancies_array = []
        children_array = []
        survey_responses_array = []
        notifications_array = []

        if export_settings and 'user_profiles' in export_settings:
            user_profiles_array = users_to_user_profiles_array(request, users)

        if export_settings and 'pregnancies' in export_settings:
            pregnancies_array = users_to_pregnancies_array(users, self.max_pregnancies())

        if export_settings and 'children' in export_settings:
            children_array = users_to_children_array(request, users, self.max_children())

        if export_settings and 'survey_responses' in export_settings:
            survey_responses_array = users_to_survey_responses_array(users, self.max_survey_responses())

        if export_settings and 'notifications' in export_settings:
            notifications_array = users_to_notifications_array(users, self.max_notifications())

        if len(users_array) > 0:
            arrays = [users_array, user_profiles_array, pregnancies_array, children_array, survey_responses_array, notifications_array]
            non_empty_arrays = [arr for arr in arrays if len(arr) > 0]
            data = np.concatenate(non_empty_arrays, axis=1)
            return np.concatenate(([self.generate_headers(export_settings)], data,)).tolist()
        else:
            return []

    def generate_headers(self, export_settings):
        headers = []

        user_labels = list(map(lambda x: verbose_name(User, x), USER_ATTRIBUTES))
        headers += user_labels

        if export_settings and 'user_profiles' in export_settings:
            user_profile_labels = list(map(lambda x: verbose_name(UserProfile, x), USER_PROFILE_ATTRIBUTES))
            headers += user_profile_labels

        if export_settings and 'pregnancies' in export_settings:
            for i in range(self.max_pregnancies()):
                labels = list(map(lambda x: f'Pregnancy {i + 1} {verbose_name(Pregnancy, x)}', PREGNANCY_ATTRIBUTES))
                headers += labels

        if export_settings and 'children' in export_settings:
            for i in range(self.max_children()):
                def _child_label(attr):
                    if attr == 'vaccinations':
                        return attr.capitalize()
                    else:
                        return verbose_name(Child, attr)
                labels = list(map(lambda x: f'Child {i + 1} {_child_label(x)}', CHILD_ATTRIBUTES))
                headers += labels

        if export_settings and 'survey_responses' in export_settings:
            for i in range(self.max_survey_responses()):
                labels = list(map(lambda x: f'Survey {i + 1} {x}', SURVEY_RESPONSE_ATTRIBUTES))
                headers += labels

        if export_settings and 'notifications' in export_settings:
            for i in range(self.max_notifications()):
                labels = list(map(lambda x: f'Notification {i + 1} {x}', NOTIFICATION_EVENT_ATTRIBUTES))
                headers += labels
                
        return headers

    @functools.cache
    def get_all_users(self):
        return User.objects.all()

    @functools.cache
    def max_pregnancies(self):
        return max(list(map(lambda x: x.pregnancy_set.count(), self.get_all_users())))

    @functools.cache
    def max_children(self):
        return max(list(map(lambda x: x.child_set.count(), self.get_all_users())))

    @functools.cache
    def max_survey_responses(self):
        return max(list(map(lambda x: x.survey_set.filter(response__isnull=False).count(), self.get_all_users())))

    @functools.cache
    def max_notifications(self):
        return max(list(map(lambda x: x.notificationevent_set.count(), self.get_all_users())))
