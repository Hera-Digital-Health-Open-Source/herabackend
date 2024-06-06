from django.db import models


class Concept(models.Model):
    name_en = models.CharField(
        max_length=255,
        unique=True
    )
    name_ar = models.CharField(
        max_length=255,
        unique=True
    )
    name_tr = models.CharField(
        max_length=255,
        unique=True
    )
    name_prs = models.CharField(
        max_length=255,
        unique=True
    )
    name_pus = models.CharField(
        max_length=255,
        unique=True
    )

    def __str__(self) -> str:
        return self.name_en


class Section(models.Model):
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    name_en = models.CharField(
        max_length=255,
        unique=True
    )
    name_ar = models.CharField(
        max_length=255,
        unique=True
    )
    name_tr = models.CharField(
        max_length=255,
        unique=True
    )
    name_prs = models.CharField(
        max_length=255,
        unique=True
    )
    name_pus = models.CharField(
        max_length=255,
        unique=True
    )
    
    def get_related_field(self, language_code):
        if language_code == "en":
            return self.name_en
        elif language_code == "ar":
            return self.name_ar
        elif language_code == "tr":
            return self.name_tr
        elif language_code == "pus":
            return self.name_pus
        elif language_code == "prs":
            return self.name_prs
        else:
            return self.name_en 

    def __str__(self) -> str:
        return f"{self.name_en} | {self.concept.__str__()}" 

class Article(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    title_en = models.CharField(
        max_length=255,
        unique=True
    )
    content_en = models.TextField()

    title_ar = models.CharField(
        max_length=255,
        unique=True
    )
    content_ar = models.TextField()

    title_tr = models.CharField(
        max_length=255,
        unique=True
    )
    content_tr = models.TextField()

    title_prs = models.CharField(
        max_length=255,
        unique=True
    )
    content_prs = models.TextField()

    title_pus = models.CharField(
        max_length=255,
        unique=True
    )
    content_pus = models.TextField()

    def get_related_fields(self, language_code):
        if language_code == "en":
            return {"title": self.title_en, "content": self.content_en}
        elif language_code == "ar":
            return {"title": self.title_ar, "content": self.content_ar}
        elif language_code == "tr":
            return {"title": self.title_tr, "content": self.content_tr}
        elif language_code == "ps":
            return {"title": self.title_ps, "content": self.content_ps}
        elif language_code == "prs":
            return {"title": self.title_prs, "content": self.content_prs}
        else:
            return {"title": self.title_en, "content": self.content_en}
        
    def __str__(self) -> str:
        return f"{self.title_en} | {self.section.name_en}" 