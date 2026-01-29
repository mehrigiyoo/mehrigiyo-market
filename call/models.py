from django.db import models
from django.conf import settings
from django.utils import timezone
from chat.models import ChatRoom


class Call(models.Model):
    """
    Unified Call Model - Voice va Video uchun
    """
    CALL_TYPE_CHOICES = (
        ('audio', 'Audio Call'),
        ('video', 'Video Call'),
    )

    STATUS_CHOICES = (
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
    )

    # Core fields
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='calls',
        db_index=True
    )
    call_type = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')

    # Participants
    caller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calls_made',
        db_index=True
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calls_received',
        db_index=True
    )

    # LiveKit integration
    livekit_room_name = models.CharField(max_length=255, unique=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    ringing_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Metrics
    duration = models.PositiveIntegerField(default=0)  # seconds
    quality_score = models.FloatField(null=True, blank=True)  # 0-5

    # Recording (future)
    recording_enabled = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True, null=True)

    # Business metrics
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # future billing

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['caller', '-created_at']),
            models.Index(fields=['receiver', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['livekit_room_name']),
            models.Index(fields=['call_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.call_type.title()} Call: {self.caller} → {self.receiver} [{self.status}]"

    def calculate_duration(self):
        """Call davomiyligini hisoblash"""
        if self.answered_at and self.ended_at:
            delta = self.ended_at - self.answered_at
            self.duration = max(0, int(delta.total_seconds()))
            self.save(update_fields=['duration'])
            return self.duration
        return 0

    def mark_status(self, status):
        """Status o'zgartirish va timestamp saqlash"""
        self.status = status

        if status == 'ringing':
            self.ringing_at = timezone.now()
        elif status == 'answered':
            self.answered_at = timezone.now()
        elif status in ['ended', 'missed', 'rejected', 'failed']:
            self.ended_at = timezone.now()
            self.calculate_duration()

        self.save()

    @property
    def is_active(self):
        """Call active ekanligini tekshirish"""
        return self.status in ['initiated', 'ringing', 'answered']

    @property
    def formatted_duration(self):
        """Duration human-readable format"""
        if not self.duration:
            return "0s"

        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60

        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class CallEvent(models.Model):
    """
    Call events tracking (for analytics & debugging)
    """
    EVENT_TYPE_CHOICES = (
        ('initiated', 'Call Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
        ('quality_changed', 'Quality Changed'),
        ('reconnecting', 'Reconnecting'),
    )

    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['call', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.call.id} - {self.event_type} by {self.user}"