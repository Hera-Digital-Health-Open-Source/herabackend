# from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from twilio.request_validator import RequestValidator
from webhook_survey_responses import utils
from hera.secrets import STATIC_TOKEN
from hera.secrets import TWILIO_AUTH_TOKEN
from django.conf import settings


class SurveyResponsesWebhookAPIView(APIView):
  """ This webhook is called when a survey response is submitted (through twilio)"""
  permission_classes = []

  def post(self, request):
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    base_url = f"https://{request.get_host()}"
    webhook_url = f"{base_url}/webhook_survey_responses/"
    
    twilio_signature = request.headers.get('X-Twilio-Signature', '')
    validation_result = validator.validate(webhook_url, request.data, twilio_signature)

    if not validation_result:
      return Response("Unauthorized", status=status.HTTP_401_UNAUTHORIZED)

    payload = request.data["ButtonPayload"].split("||")
    input_vaccine_names = []

    if len(payload) == 4:
      # the 'no' case
      input_vaccine_names = payload[2].split(", ")
    else:
      # the 'yes' case
      input_vaccine_names = payload[2].split(", ")

    answer = utils.handle_response(request.data["ButtonText"])
    matched_vaccine_ids = utils.get_matched_vaccine_ids(base_url, STATIC_TOKEN, input_vaccine_names)

    child_id = 0

    if answer == "yes":
      child_id = payload[2]
    else:
      child_id = payload[3]
    
    utils.update_child_past_vaccination(base_url, STATIC_TOKEN, matched_vaccine_ids, child_id)

    survey_id = payload[0]
    utils.update_survey_response(base_url, STATIC_TOKEN, survey_id, answer)

    return Response("OK", status=status.HTTP_201_CREATED)
