from django.urls import path

from whatsapp_opt_history import views

urlpatterns = [
    path('whatsapp_opt_in_out/', views.WhatsAppOptInOutView.as_view()),
]