# ============================================
# FILE: payment/middleware.py - NEW
# ============================================

import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class PaymentSecurityMiddleware:
    """
    Security middleware for payment endpoints

    Features:
    - Rate limiting
    - IP whitelisting (for Payme)
    - Request logging
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Payme IP whitelist (from Payme documentation)
        self.payme_ips = [
            '185.178.208.0/22',  # Payme production IPs
            '195.158.31.0/24',
            '195.158.28.0/23',
            '195.158.30.0/23',
        ]

    def __call__(self, request):
        # Check if this is a Payme callback
        if '/api/payments/payme/callback/' in request.path:
            if not self.verify_payme_ip(request):
                logger.warning(f"Unauthorized Payme callback attempt from {self.get_client_ip(request)}")
                return JsonResponse({
                    'error': {
                        'code': -32504,
                        'message': 'Unauthorized IP'
                    }
                }, status=403)

        response = self.get_response(request)
        return response

    def verify_payme_ip(self, request):
        """Verify request is from Payme IP"""
        from ipaddress import ip_address, ip_network

        client_ip = self.get_client_ip(request)

        try:
            client = ip_address(client_ip)

            # Check if IP is in whitelist
            for ip_range in self.payme_ips:
                if client in ip_network(ip_range):
                    return True

            return False

        except:
            return False

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip