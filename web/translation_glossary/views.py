import json
from django.http import JsonResponse
from rest_framework.decorators import action
from django.views.generic import TemplateView
import os
import html

from google.cloud import translate_v2


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"google-tranlation-glossary-api-key.json"


class TranslateView(TemplateView):

    @action(detail=True, methods=['post'])
    def post(self, request):
        translate_model = translate_v2.Client()
        data = json.loads(request.body)

        response = translate_model.translate(
            data['content'], target_language=data['target'], source_language=data['source'])

        decoded_result = {
            "input": response["input"],
            "translated_text": html.unescape(
                response["translatedText"]),
            "target_language": data['target'],
            "source_language": data['source']
        }

        return JsonResponse(decoded_result)
