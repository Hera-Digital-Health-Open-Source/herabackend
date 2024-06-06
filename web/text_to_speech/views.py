import json
from django.http import JsonResponse
from rest_framework.decorators import action
from django.views.generic import TemplateView
from google.cloud import texttospeech
import base64
from django.http import HttpResponse

key_path = r"google-tranlation-glossary-api-key.json"

class TextToSpeechView(TemplateView):

    @action(detail=True, methods=['get'])
    def get(self, request):
        client = texttospeech.TextToSpeechClient.from_service_account_json(key_path)
        input_text = texttospeech.SynthesisInput(text=request.GET.get('content'))

        voice = texttospeech.VoiceSelectionParams(
            language_code=request.GET.get('source'), ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )

        response = HttpResponse(response.audio_content, content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="output.mp3"'
        return response
    