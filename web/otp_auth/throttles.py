from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle

from otp_auth.exceptions import InvalidPhoneNumberException
from otp_auth.utils import sanitize_phone_number


class RequestOtpIpBasedThrottle(AnonRateThrottle):
    """
    Limits the burst rate of OTP that can be requested from one IP address
    """
    rate = '60/min'
    scope = 'burst'


class RequestOtpIpBasedDailyThrottle(AnonRateThrottle):
    """
    Limits the sustained rate of OTP that can be requested from one IP address
    """
    rate = '120/day'
    scope = 'sustained'



class RequestOtpPhoneNumberBasedThrottle(SimpleRateThrottle):
    """
    Limits the rate of OTP that can be requested for specified phone number.
    """
    scope = 'phone'
    rate = '2/min'

    def get_cache_key(self, request: Request, view):
        if "phone_number" not in request.data:
            return None
        try:
            phone_number = request.data["phone_number"]
            clean_phone_number = sanitize_phone_number(phone_number)
        except InvalidPhoneNumberException:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': clean_phone_number
        }
