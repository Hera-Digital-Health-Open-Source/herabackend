from django.db import models


class Translation(models.Model):
  """
      This table will be used to store translations between languages that the 
      app supports.
  """
  entry_en = models.TextField(unique=True, null=True, blank=True)
  entry_ar = models.TextField(unique=True, null=True, blank=True)
  entry_tr = models.TextField(unique=True, null=True, blank=True)
  entry_prs = models.TextField(unique=True, null=True, blank=True)
  entry_pus = models.TextField(unique=True, null=True, blank=True)
