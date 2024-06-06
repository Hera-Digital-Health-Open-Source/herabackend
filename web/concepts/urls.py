from django.urls import path
from concepts import views

urlpatterns = [
    path('concepts/<int:concept_id>/sections/', views.ConceptSectionsAPIView.as_view(), name='concept_sections'),
    path('articles/<int:article_id>/', views.ArticlesAPIView.as_view(), name='articles'),
    path('concepts/<int:concept_id>/<str:language_code>/sections/', views.ConceptSectionsAPIView.as_view(), name='concept_sections'),
    path('articles/<int:article_id>/<str:language_code>/', views.ArticlesAPIView.as_view(), name='articles'),
]