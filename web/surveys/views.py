from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from surveys.models import Survey, SurveyTemplate
from surveys.serializers import SurveyResponseSerializer, SurveySerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from surveys.utils import process_survey_after_response_created
from hera.secrets import STATIC_TOKEN


class SurveyResponseView(APIView):
    permission_classes = [IsAuthenticated or IsAdminUser]

    def post(self, request, survey_id):
        survey = SurveyTemplate.objects.filter(id=survey_id, user=self.request.user.id)
        if (survey):
            serializer = SurveyResponseSerializer(data={"user": self.request.user.id, "survey": survey_id, "response": request.data["response"]})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response("Survey not found", status=status.HTTP_400_BAD_REQUEST)


class SurveyViewSet(ReadOnlyModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated or IsAdminUser]

    def get_queryset(self):
        request_token = self.request.headers["Authorization"]
        if request_token == STATIC_TOKEN:
            survey_id = self.request.path_info.split('/')[-3]
            return self.queryset.filter(id = survey_id)
        return self.queryset.filter(user=self.request.user)

    def get_serializer_context(self):
        request_token = self.request.headers["Authorization"]
        if request_token == STATIC_TOKEN:
            return
        return {'language_code': self.request.user.userprofile.language_code}

    @extend_schema(responses=SurveySerializer(many=True))
    @action(detail=False, methods=['get'])
    def pending(self, request):
        queryset = self.get_queryset().filter(response__isnull=True).order_by('id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], serializer_class=SurveyResponseSerializer)
    def response(self, request, pk=None):
        survey: Survey = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_code = serializer.validated_data["response"]
        valid_options = survey.survey_template.surveytemplateoption_set.all()
        valid_option_codes = [option.code for option in valid_options]
        if response_code in valid_option_codes:
            survey.response = response_code
            survey.responded_at = timezone.now()
            survey.save()
            process_survey_after_response_created(survey)
            return Response(status=200)
        else:
            raise ValidationError(f"Invalid response. Must be one of the following: {valid_option_codes}")


class SurveyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Survey.objects.filter(user=self.request.user)
        serializer = SurveySerializer(queryset, many=True, context={'language_code': self.request.user.userprofile.language_code})
        return Response(serializer.data, status=status.HTTP_200_OK)
