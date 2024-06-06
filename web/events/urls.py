from django.urls import path
from rest_framework import routers

from events import views


router = routers.SimpleRouter()
router.register('notification_events', views.NotificationEventViewSet, basename='events.notifications')

urlpatterns = [
    *router.urls,
    path('calendar_events/', views.CalendarEventView.as_view()),
]
