from rest_framework import serializers
from concepts import models


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Article
        fields = ('id', 'title_en', 'title_ar', 'title_tr', 'title_prs', 'title_pus')


class SectionSerializer(serializers.ModelSerializer):
    articles = ArticleSerializer(many=True, read_only=True)

    class Meta:
        model = models.Section
        fields = ('name_en', 'name_ar', 'name_tr', 'name_prs', 'name_pus', 'articles')
