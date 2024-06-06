from secrets import randbelow
import os
import phonenumbers
from django.utils.translation import gettext_lazy as _
from phonenumbers.phonenumberutil import NumberParseException

from otp_auth.exceptions import InvalidPhoneNumberException


def generate_secret(otp_length: int) -> str:
    assert otp_length >= 1
    exclusive_upper_bound = 10 ** otp_length
    return str(randbelow(exclusive_upper_bound)).rjust(otp_length, '0')


def sanitize_phone_number(phone_number: str) -> str:
    try:
        parsed_phone_number = phonenumbers.parse(phone_number)
    except NumberParseException as error:
        raise InvalidPhoneNumberException(str(error))
    is_valid_phone_number = phonenumbers.is_valid_number(parsed_phone_number)
    if not is_valid_phone_number:
        raise InvalidPhoneNumberException(_("The text you entered is not a valid phone number"))
    clean_phone_number = phonenumbers.format_number(parsed_phone_number, phonenumbers.PhoneNumberFormat.E164)
    return clean_phone_number


def get_error_message_from_number_parse_exception(error: NumberParseException):
    match error.error_type:
        case NumberParseException.INVALID_COUNTRY_CODE:
            return _("The phone number you entered has an invalid country code. Please select the right country.")
        case NumberParseException.NOT_A_NUMBER:
            return _("The text you entered is not a correct phone number. Please check again.")
        case NumberParseException.TOO_SHORT_NSN | NumberParseException.TOO_SHORT_AFTER_IDD:
            return _("The phone number you entered is too short.")
        case NumberParseException.TOO_LONG:
            return _("The phone number you entered is too long.")
