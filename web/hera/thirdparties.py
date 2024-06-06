import messagebird
import onesignal_sdk.client

from hera.secrets import *
from twilio.rest import Client

messagebird_client = messagebird.Client(MESSAGEBIRD_API_KEY)
onesignal_client = onesignal_sdk.client.Client(
	app_id=ONESIGNAL_ID,
	rest_api_key=ONESIGNAL_KEY,
)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)