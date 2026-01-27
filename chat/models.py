from django.db import models
from account.models import UserModel
import datetime

today = datetime.date.today()

class ChatRoom(models.Model):
    participants = models.ManyToManyField(
        UserModel,
        related_name='chat_rooms'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def __str__(self):
        return f"ChatRoom {self.id}"


class Message(models.Model):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    text = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
        ]


    def __str__(self):
        return f"{self.sender.phone}: {self.text[:20]}"



class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='messages/files/')
    file_type = models.CharField(
        max_length=20,
        choices=(
            ('image', 'Image'),
            ('video', 'Video'),
            ('file', 'File'),
        )
    )
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

