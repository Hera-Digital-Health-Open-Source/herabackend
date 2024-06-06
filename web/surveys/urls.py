from django.urls.conf import path
from rest_framework import routers
from surveys.views import SurveyResponseView, SurveyView, SurveyViewSet


router = routers.SimpleRouter()
router.register('surveys', SurveyViewSet, basename='surveys.surveys')

urlpatterns = router.urls
