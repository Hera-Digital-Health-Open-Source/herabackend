from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from whatsapp_opt_history import serializers
from events.models import InstantNotification, NotificationType
from whatsapp_opt_history import utils

class WhatsAppOptInOutView(APIView):
    """ Handling opt-ins and opt-outs requests for whatsapp notifications """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        serializer = serializers.WhatsAppOptInOutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            matched_notification_type = None
            if serializer.validated_data.get('opt_status') == 'opt_in':
                matched_notification_type = NotificationType.objects.filter(code="whatsapp_opt_in_confirmation_template").first()
            if matched_notification_type:
                instantNotification = InstantNotification(phone_numbers=[serializer.validated_data.get('username')], notification_type=matched_notification_type)
                instantNotification.save()
            return Response(
                {
                    'opt_status': serializer.validated_data.get('opt_status')
                },
                status=201
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request: Request):
        username = request.query_params.get('username')
        if username == None or username == '':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if username[0] != '+':
            if username[0] not in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                username = '+' + username[1:]
            else:
                username = '+' + username
        is_opt_in = utils.is_user_opt_in(username)
        opt_status = None
        if is_opt_in:
            opt_status = 'opt_in'
        else:
            opt_status = 'opt_out'
        
        return Response(
            {
                'opt_status': opt_status 
            },
            status=200
        )
