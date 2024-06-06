from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from child_health.filters import PregnancyFilter
from child_health.models import Child, Pregnancy, Vaccine
from child_health.serializers import ChildSerializer, PregnancySerializer, VaccineSerializer
from translation_glossary.utils import translate_entries

from hera.secrets import STATIC_TOKEN

class PregnancyViewSet(ModelViewSet):
    queryset = Pregnancy.objects.all()
    serializer_class = PregnancySerializer
    permission_classes = [IsAuthenticated or IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PregnancyFilter

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        active_pregnancy = Pregnancy.objects.get_active_pregnancy_for_user(request.user)
        if active_pregnancy is not None:
            serializer = self.get_serializer(active_pregnancy, many=False)
            return Response(serializer.data)
        return Response(status=404)


class ChildrenViewSet(ModelViewSet):
    queryset = Child.objects.all()
    serializer_class = ChildSerializer
    permission_classes = [IsAuthenticated or IsAdminUser]

    def get_queryset(self):
        request_token = self.request.headers['Authorization']
        if request_token == STATIC_TOKEN:
            child_id = self.request.path_info.split('/')[-2]
            return self.queryset.filter(id=child_id)

        return self.queryset.filter(user=self.request.user)


class VaccinesViewSet(ListModelMixin, GenericViewSet):
    queryset = Vaccine.objects.all()
    serializer_class = VaccineSerializer
    permission_classes = [IsAuthenticated or IsAdminUser]

    def get_queryset(self):
        active_vaccines = self.queryset.filter(is_active=True)
        active_vaccines_names = list(active_vaccines.values_list('name', flat=True))
        destinationLanguage = ""
        
        # If the user's location is in Turkey, and his language_code is Arabic then
        # return vaccine names only in Turkish.
        if self.request.user.userprofile.timezone == "Europe/Istanbul" \
            and self.request.user.userprofile.language_code == "ar":
            destinationLanguage = "tr"
        else:
            destinationLanguage = self.request.user.userprofile.language_code

        translations = translate_entries(
                active_vaccines_names,
                "en",
                destinationLanguage
            )
        
        for active_vaccine in active_vaccines:
            active_vaccine.name = [x[1] for x in translations if active_vaccine.name == x[0]][0]
        return active_vaccines
