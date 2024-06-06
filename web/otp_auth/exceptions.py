from rest_framework.exceptions import APIException


class InvalidPhoneNumberException(APIException):
    status_code = 400

class MessageBirdNotSupportedCountryException(APIException):
    status_code = 498
    default_detail = 'Sorry, your country is not supported right now! In the meantime, do visit https://heradigitalhealth.org to learn more about our work'

    def __init__(self, detail=None, code=None):
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code
        super().__init__(detail=detail, code=code)