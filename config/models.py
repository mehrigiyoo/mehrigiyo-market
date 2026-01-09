from django.db import models

# Create your models here.

class ConfigModel(models.Model):
    version = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        return f"{self.version}"
