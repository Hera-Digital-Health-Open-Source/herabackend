from django.conf import settings
from django.http import request
from rest_framework.fields import CharField, ListField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer

from surveys.models import Survey, SurveyTemplateOption


class SurveyOptionSerializer(ModelSerializer):
    translated_text = SerializerMethodField()

    class Meta:
        model = SurveyTemplateOption
        fields = ['code', 'translated_text']

    def get_translated_text(self, obj):
        language_code = self.context['language_code']
        match language_code:
            case 'en':
                return obj.option_en
            case 'ar':
                return obj.option_ar
            case 'tr':
                return obj.option_tr


class SurveySerializer(ModelSerializer):
    options = ListField(
        child=SurveyOptionSerializer(),
        source='survey_template.surveytemplateoption_set.all',
    )

    class Meta:
        model = Survey
        fields = [
            'id',
            'survey_type',
            'question',
            'response',
            'responded_at',
            'options',
            'context',
        ]


class SurveyResponseSerializer(Serializer):
    response = CharField(max_length=20)
