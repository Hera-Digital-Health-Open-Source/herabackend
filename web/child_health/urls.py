from rest_framework import routers

from child_health.views import PregnancyViewSet, ChildrenViewSet, VaccinesViewSet


router = routers.SimpleRouter()
router.register('pregnancies', PregnancyViewSet, basename='child_health.pregnancies')
router.register('children', ChildrenViewSet, basename='child_health.children')
router.register('vaccines', VaccinesViewSet, basename='child_health.vaccines')

urlpatterns = router.urls
