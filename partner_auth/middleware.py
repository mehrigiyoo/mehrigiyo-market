from django.core.cache import cache
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from .models import PartnerRequest
import json


class PartnerRateLimitMiddleware:
    """Partner uchun rate limiting"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Faqat partner API endpointlari uchun
        if hasattr(request, 'partner') and request.partner:
            if not self.check_rate_limit(request.partner):
                return Response(
                    {"detail": "Rate limit exceeded. Too many requests."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

        response = self.get_response(request)

        # Partner so'rovlarini log qilish
        if hasattr(request, 'partner') and request.partner:
            self.log_partner_request(request, response)

        return response

    def check_rate_limit(self, partner):
        """Rate limit tekshirish"""
        cache_key = f"partner_rate_limit_{partner.id}"
        current_minute = timezone.now().strftime("%Y-%m-%d-%H-%M")
        full_cache_key = f"{cache_key}_{current_minute}"

        # Hozirgi minutdagi so'rovlar sonini olish
        request_count = cache.get(full_cache_key, 0)

        if request_count >= partner.rate_limit_per_minute:
            return False

        # So'rovlar sonini oshirish
        cache.set(full_cache_key, request_count + 1, 60)  # 60 soniya
        return True

    def log_partner_request(self, request, response):
        """Partner so'rovini log qilish"""
        try:
            # Request body ni olish
            request_data = None
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    request_data = json.loads(request.body.decode('utf-8'))
                    # Sensitiv ma'lumotlarni olib tashlash
                    if isinstance(request_data, dict):
                        request_data.pop('password', None)
                        request_data.pop('api_secret', None)
                except:
                    pass

            # Response data ni olish
            response_data = None
            if hasattr(response, 'data'):
                response_data = response.data

            # IP address olish
            ip_address = self.get_client_ip(request)

            # User phone (agar mavjud bo'lsa)
            user_phone = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_phone = getattr(request.user, 'phone', None)

            # Log yaratish
            PartnerRequest.objects.create(
                partner=request.partner,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                user_phone=user_phone,
                ip_address=ip_address,
                request_data=request_data,
                response_data=response_data
            )

            # Partner statistikasini yangilash
            request.partner.total_requests += 1
            request.partner.save(update_fields=['total_requests'])

        except Exception as e:
            # Log xatosi asosiy jarayonga ta'sir qilmasligi kerak
            print(f"Partner request logging error: {e}")

    def get_client_ip(self, request):
        """Client IP manzilini olish"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip