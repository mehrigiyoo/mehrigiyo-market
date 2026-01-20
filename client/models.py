from django.db import models

from account.models import UserModel


# account/models.py
class ClientProfile(models.Model):
    user = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )
    full_name = models.CharField(max_length=255, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=(('male', 'Male'), ('female', 'Female')),
        null=True, blank=True
    )
    birthday = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Client: {self.user.phone}"
