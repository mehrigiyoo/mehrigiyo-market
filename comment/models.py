from django.db import models
from django.db.models import UniqueConstraint

from account.models import UserModel
from shop.models import Medicine
from specialist.models import Doctor


class CommentMedicine(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.RESTRICT, related_name='comments_med')
    user = models.ForeignKey(UserModel, on_delete=models.RESTRICT)
    text = models.TextField()
    rate = models.SmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['medicine', 'user'], name='rate_med')
        ]


class CommentDoctor(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT, related_name='comments_doc')
    user = models.ForeignKey(UserModel, on_delete=models.RESTRICT)
    text = models.TextField(null=True, blank=True)
    rate = models.SmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['doctor', 'user'], name='rate_doc')
        ]


class QuestionModel(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    question = models.CharField(max_length=255)
    answer = models.BooleanField(default=False)
