from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from .models import Partner


def authenticate_partner(view_func):
    """
    Partner authentication decorator
    API Key va API Secret orqali partnerni tekshiradi
    """

    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        api_secret = request.headers.get('X-API-Secret')

        if not api_key or not api_secret:
            return Response(
                {"detail": "API Key va API Secret headerlarida yuborilishi kerak"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            partner = Partner.objects.get(api_key=api_key, is_active=True)
        except Partner.DoesNotExist:
            return Response(
                {"detail": "Noto'g'ri API Key"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Secret ni tekshirish
        if not partner.verify_secret(api_secret):
            return Response(
                {"detail": "Noto'g'ri API Secret"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Partner obyektini request ga qo'shamiz
        request.partner = partner

        return view_func(self, request, *args, **kwargs)

    return wrapper


class IsPartnerAuthenticated(BasePermission):
    """
    DRF permission class - partner autentifikatsiyasini tekshiradi
    """

    def has_permission(self, request, view):
        api_key = request.headers.get('X-API-Key')
        api_secret = request.headers.get('X-API-Secret')

        if not api_key or not api_secret:
            return False

        try:
            partner = Partner.objects.get(api_key=api_key, is_active=True)
        except Partner.DoesNotExist:
            return False

        if not partner.verify_secret(api_secret):
            return False

        # Partner obyektini request ga qo'shamiz
        request.partner = partner
        return True

    def has_object_permission(self, request, view, obj):
        return True