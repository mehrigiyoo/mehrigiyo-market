from django.db import models
from django.conf import settings
import os


class ChatRoom(models.Model):
    ROOM_TYPE_CHOICES = (
        ('1:1', 'One to One'),
        ('group', 'Group'),
    )
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default='1:1')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


    # Last message cache (tezlik uchun)
    last_message_text = models.TextField(blank=True, null=True)
    last_message_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['room_type']),
        ]

    def __str__(self):
        return f"Room {self.id} ({self.room_type})"

    @classmethod
    def get_or_create_private_room(cls, user1, user2):
        # Ikkala user ishtirok etgan room topish
        rooms = cls.objects.filter(
            room_type='1:1',
            participants=user1
        ).filter(
            participants=user2
        )

        if rooms.exists():
            return rooms.first(), False  # Mavjud room

        # Yangi room yaratish
        room = cls.objects.create(room_type='1:1', created_by=user1)
        room.participants.add(user1, user2)  #  IKKALA USERNI QO'SHADI
        return room, True

    def get_unread_count(self, user):
        """User uchun o'qilmagan xabarlar soni"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def get_other_participant(self, user):
        """1:1 chatda ikkinchi user"""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
    )

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    text = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Reply uchun
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f"{self.sender.phone}: {self.text[:20]}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Room last message update
        if is_new:
            self.room.last_message_text = self.text[:100] if self.text else f"[{self.message_type}]"
            self.room.last_message_time = self.created_at
            self.room.save(update_fields=['last_message_text', 'last_message_time', 'updated_at'])


class MessageAttachment(models.Model):
    FILE_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
    )

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_name = models.CharField(max_length=255)
    size = models.PositiveIntegerField()  # bytes
    duration = models.PositiveIntegerField(null=True, blank=True)  # audio/video uchun (seconds)
    thumbnail = models.ImageField(upload_to='chat_thumbnails/%Y/%m/%d/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.file_type}: {self.file_name}"

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None

    @property
    def thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return None

    def get_file_extension(self):
        return os.path.splitext(self.file_name)[1].lower()