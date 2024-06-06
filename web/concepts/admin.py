from django.contrib import admin
from concepts import models

admin.site.register(models.Concept)
admin.site.register(models.Section)
admin.site.register(models.Article)
