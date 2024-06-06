from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.fields import DateField, CharField, IntegerField, ListField
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from events.utils import generate_all_calendar_events_for_user
from events.models import NotificationEvent
from events.serializers import NotificationEventSerializer
from translation_glossary.utils import translate_entries

class CalendarEventView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[],
        request=None,
        responses=inline_serializer(
            name='Calendar Event',
            fields={
                'date': DateField(help_text='The date of the event'),
                'event_type': CharField(help_text='Either `vaccination` or `prenatal_checkup`'),
                'weeks_pregnant': IntegerField(help_text='For prenatal_checkup event only. The number of weeks the '
                                                         'mother is pregnant at the time of checkup.'),
                'week_age': IntegerField(help_text="For vaccination event only. The child's age in weeks at the time "
                                                   "of vaccination."),
                'person_name': CharField(help_text="For vaccination event only. The name of the person affected by the event."),
                'vaccine_names': ListField(
                    child=CharField(),
                    help_text="For vaccination event only. The name of the vaccine(s) to be administered.",
                ),
            },
        ),
    )

    def get(self, request: Request):
        user = request.user
        calendar_events = generate_all_calendar_events_for_user(user)
        data = list([e.to_dictionary() for e in calendar_events])
        destinationLanguage = ""
        for item in data:
            if "vaccine_names" in item:
                vaccine_names = item["vaccine_names"]
                
                # If the user's location is in Turkey, and his language_code is Arabic then
                # return vaccine names only in Turkish.
                if user.userprofile.timezone == "Europe/Istanbul" \
                    and user.userprofile.language_code == "ar":
                    destinationLanguage = "tr"
                else:
                    destinationLanguage = user.userprofile.language_code
                translations = translate_entries(vaccine_names, "en", destinationLanguage)
                item["vaccine_names"] = [x[1] for x in translations]
        return Response(
            status=200,
            data=data,
        )


class NotificationEventViewSet(ListModelMixin, GenericViewSet):
    queryset = NotificationEvent.objects.all()
    serializer_class = NotificationEventSerializer
    permission_classes = [IsAuthenticated]
    ordering = ('-id',)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    @extend_schema(
        parameters=[],
        request=None,
        responses=None,
    )
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        user = request.user
        user.notificationevent_set.update(read_at=timezone.now())
        return Response(status=200)
