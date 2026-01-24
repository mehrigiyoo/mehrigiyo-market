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


class ClientAddress(models.Model):
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    address_line = models.CharField(max_length=255)
    home = models.CharField(max_length=100, blank=True, null=True)
    entrance = models.CharField(max_length=50, blank=True, null=True)
    floor = models.CharField(max_length=50, blank=True, null=True)
    apartment = models.CharField(max_length=50, blank=True, null=True)
    add_phone = models.CharField(max_length=50, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
