from django.db import models
from django.utils.crypto import get_random_string
import hashlib


class Partner(models.Model):
    """Hamkor ilovalar uchun model"""
    name = models.CharField(max_length=255, unique=True, verbose_name="Hamkor nomi")
    api_key = models.CharField(max_length=100, unique=True, verbose_name="API Key")
    api_secret = models.CharField(max_length=255, verbose_name="API Secret (hashed)")

    is_active = models.BooleanField(default=True, verbose_name="Faol")

    # Rate limiting
    rate_limit_per_minute = models.IntegerField(default=60, verbose_name="Minutiga so'rovlar soni")

    # Statistika
    total_requests = models.IntegerField(default=0, verbose_name="Jami so'rovlar")
    total_users_created = models.IntegerField(default=0, verbose_name="Yaratilgan userlar")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'partners'
        verbose_name = 'Hamkor'
        verbose_name_plural = 'Hamkorlar'

    def __str__(self):
        return self.name

    @staticmethod
    def hash_secret(secret):
        """Secret ni hash qilish"""
        return hashlib.sha256(secret.encode()).hexdigest()

    def verify_secret(self, secret):
        """Secret ni tekshirish"""
        return self.api_secret == self.hash_secret(secret)

    @classmethod
    def generate_credentials(cls):
        """Yangi credentials yaratish"""
        api_key = f"pk_live_{get_random_string(32)}"
        api_secret = f"sk_live_{get_random_string(48)}"
        return api_key, api_secret

    def save(self, *args, **kwargs):
        # Agar yangi partner bo'lsa va api_key yo'q bo'lsa, generate qilamiz
        if not self.pk and not self.api_key:
            self.api_key, secret = self.generate_credentials()
            self.api_secret = self.hash_secret(secret)
            print(f"⚠️ IMPORTANT: Save this secret for {self.name}: {secret}")
            print(f"API Key: {self.api_key}")
        super().save(*args, **kwargs)


class PartnerRequest(models.Model):
    """Hamkor so'rovlarini logging qilish"""
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='requests')
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()

    user_phone = models.CharField(max_length=20, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'partner_requests'
        verbose_name = 'Hamkor so\'rovi'
        verbose_name_plural = 'Hamkor so\'rovlari'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['partner', '-created_at']),
        ]