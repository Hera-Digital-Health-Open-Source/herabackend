from django.shortcuts import render
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from concepts.models import Section, Concept, Article
from concepts.serializers import SectionSerializer, ArticleSerializer


class ConceptSectionsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, concept_id, language_code=''):
        try:
            concept = Concept.objects.get(pk=concept_id)
        except Concept.DoesNotExist:
            return Response({"error": "Concept is not found"}, status=status.HTTP_404_NOT_FOUND)

        if language_code is None or language_code == '':
            language_code = request.user.userprofile.language_code

        sec = Section.objects.filter(concept=concept).order_by('order')
        sections = map(lambda x: {"id": x.id, "name": x.get_related_field(language_code)}, sec)
        section_data = []

        for section in sections:
            articles = Article.objects.filter(section__id=section["id"]).order_by('order')
            article_data = ArticleSerializer(articles, many=True).data
            article_data_mapped = map(lambda x: {"id": x["id"], "title": x["title_" + language_code]}, article_data)

            section_data.append({
                "name": section["name"],
                "articles": article_data_mapped
            })

        return Response(section_data, status=status.HTTP_200_OK)


class ArticlesAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, article_id, language_code=''):
        try:
            article = Article.objects.get(pk=article_id)
        except Article.DoesNotExist:
            return Response({"error": "Article is not found"}, status=status.HTTP_404_NOT_FOUND)

        if language_code is None or language_code == '':
            language_code = request.user.userprofile.language_code
        
        related_fields = article.get_related_fields(language_code)
        article_data_dict = {"id": article.id, "title": related_fields["title"], "content": related_fields["content"]}

        return Response(article_data_dict, status=status.HTTP_200_OK)