from rest_framework.throttling import SimpleRateThrottle


class ChangePhoneNumberRequestThrottle(SimpleRateThrottle):
    scope = 'change_phone_number_request'
    rate = '1/hour'

    def get_cache_key(self, request, view):
        if request.method == "GET":
            return None
        user_id = request.user.id
        return self.cache_format % {
            'scope': self.scope,
            'ident': user_id,
        }


class ChangePhoneNumberRequestResendOtpThrottle(SimpleRateThrottle):
    scope = 'change_phone_number_request_resend_sms'
    rate = '1/min'

    def get_cache_key(self, request, view):
        user_id = request.user.id
        return self.cache_format % {
            'scope': self.scope,
            'ident': user_id,
        }