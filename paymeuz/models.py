# ============================================
# FILE: payment/models.py - COMPLETE
# ============================================

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


class Payment(models.Model):
    """
    Universal payment model
    Supports: Market orders + Consultations
    """

    PAYMENT_TYPE_CHOICES = (
        ('market', 'Market Order'),  # Product purchase
        ('consultation', 'Consultation'),  # Doctor consultation
    )

    PAYMENT_METHOD_CHOICES = (
        ('payme', 'Payme'),
        ('click', 'Click'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),  # Created, waiting for payment
        ('processing', 'Processing'),  # Payment in progress
        ('paid', 'Paid'),  # Successfully paid
        ('failed', 'Failed'),  # Payment failed
        ('cancelled', 'Cancelled'),  # Cancelled by user
        ('refunded', 'Refunded'),  # Refunded
    )

    # Unique payment ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    # Payment type (market or consultation)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)

    # Polymorphic relation (links to Order or ConsultationRequest)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Payment details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='UZS')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Payme specific fields
    payme_transaction_id = models.CharField(max_length=255, blank=True, db_index=True)
    payme_time = models.BigIntegerField(null=True, blank=True)  # Unix timestamp from Payme
    payme_state = models.IntegerField(null=True, blank=True)  # Payme state (1,2,etc)
    payme_reason = models.IntegerField(null=True, blank=True)  # Cancel reason

    # Security & Audit
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Gateway response (full JSON)
    gateway_response = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_type', 'status']),
            models.Index(fields=['payme_transaction_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.payment_type} - {self.amount} UZS"

    def mark_as_paid(self, transaction_id=None):
        """Mark payment as successful"""
        from django.utils import timezone

        self.status = 'paid'
        self.paid_at = timezone.now()

        if transaction_id:
            self.payme_transaction_id = transaction_id

        self.save()

        # Trigger signal
        # from .signals import payment_success
        # payment_success.send(sender=self.__class__, payment=self)

    def mark_as_failed(self, reason=''):
        """Mark payment as failed"""
        self.status = 'failed'
        self.metadata['failure_reason'] = reason
        self.save()

        # from .signals import payment_failed
        # payment_failed.send(sender=self.__class__, payment=self)

    def can_cancel(self):
        """Check if payment can be cancelled"""
        return self.status in ['pending', 'processing']

    def cancel(self, reason=''):
        """Cancel payment"""
        from django.utils import timezone

        if not self.can_cancel():
            raise ValueError(f"Cannot cancel payment with status {self.status}")

        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.metadata['cancel_reason'] = reason
        self.save()


class PaymentTransaction(models.Model):
    """
    Payme transaction log
    Tracks all Payme API calls for audit
    """

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_id = models.CharField(max_length=255, db_index=True)

    # Payme method called
    method = models.CharField(max_length=50)  # CheckPerformTransaction, CreateTransaction, etc

    # Request/Response
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)

    # State changes
    state = models.IntegerField(null=True, blank=True)
    reason = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']