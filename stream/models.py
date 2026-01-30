from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from account.models import UserModel


class LiveStream(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    )

    # Core
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    host = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='hosted_streams')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='live', db_index=True)
    livekit_room_name = models.CharField(max_length=255, unique=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)

    # Metrics
    viewer_count = models.IntegerField(default=0)
    peak_viewers = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)

    # Features
    recording_enabled = models.BooleanField(default=False)
    recording_url = models.URLField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='streams/%Y/%m/', null=True, blank=True)
    chat_enabled = models.BooleanField(default=True)
    reactions_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['host', '-created_at']),
        ]

    def __str__(self):
        return self.title

    @property
    def cache_key_viewers(self):
        return f'stream:{self.id}:viewers'

    def get_active_viewers(self):
        viewers = cache.get(self.cache_key_viewers, set())
        return len(viewers) if isinstance(viewers, set) else 0

    def add_viewer(self, user_id):
        viewers = cache.get(self.cache_key_viewers, set())
        viewers.add(user_id)
        cache.set(self.cache_key_viewers, viewers, 7200)
        count = len(viewers)
        if count > self.peak_viewers:
            self.peak_viewers = count
        self.viewer_count = count
        self.save(update_fields=['viewer_count', 'peak_viewers'])

    def remove_viewer(self, user_id):
        viewers = cache.get(self.cache_key_viewers, set())
        viewers.discard(user_id)
        cache.set(self.cache_key_viewers, viewers, 7200)
        self.viewer_count = len(viewers)
        self.save(update_fields=['viewer_count'])

    def start_stream(self):
        self.status = 'live'
        self.started_at = timezone.now()
        self.save()
        cache.delete(self.cache_key_viewers)

    def end_stream(self):
        self.status = 'ended'
        self.ended_at = timezone.now()
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration = int(delta.total_seconds())
        self.save()
        cache.delete(self.cache_key_viewers)


class StreamViewer(models.Model):
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='viewers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    watch_duration = models.IntegerField(default=0)
    device_type = models.CharField(max_length=50, blank=True, default='')


    class Meta:
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['stream', 'user']),
        ]


class StreamChat(models.Model):
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['stream', '-created_at']),
        ]


class StreamReaction(models.Model):
    REACTION_CHOICES = (
        ('like', '❤️'),
        ('fire', '🔥'),
        ('clap', '👏'),
        ('wow', '😮'),
    )

    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['stream', 'user', 'reaction_type']