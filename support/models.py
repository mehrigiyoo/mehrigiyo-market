from django.db import models
from account.models import UserModel

class Operator(models.Model):
    user = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE,
        related_name='operator_profile'
    )
    full_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='operators/', null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=(('male', 'Male'), ('female', 'Female'))
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Operator: {self.full_name}"
