from django.contrib.auth.models import User
from django.conf import settings


class ReadLanguageFromUserProfileMiddleware:
    __slots__ = ['get_response']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_anonymous:
            return self.get_response(request)
        try:
            user_language_code = request.user.userprofile.language_code
            request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = user_language_code
        except User.userprofile.RelatedObjectDoesNotExist:
            pass
        return self.get_response(request)
