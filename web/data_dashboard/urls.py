from django.urls import path
from rest_framework import routers
from data_dashboard import views


router = routers.SimpleRouter()
router.register('data_dashboard', views.UsersDataDashboardViewSet, basename='data_dashboard.users')
router.register('data_dashboard', views.UserCustomAuthenticationViewSet, basename='data_dashboard.auth')
router.register('data_dashboard', views.PregnancyDataDashboardViewSet, basename='data_dashboard.pregnancy')
router.register('data_dashboard', views.VaccinationDataDashboardViewSet, basename='data_dashboard.vaccination')
# router.register('data_dashboard', views.UserCustomAuthenticationViewSet, basename='data_dashboard.logout')

urlpatterns = router.urls



# urlpatterns = [
#     path('data_dashboard/users/', views.UsersDataDashboardView.as_view()),
#     path('data_dashboard/login/', views.UserCustomAuthentication.as_view()),
# ]