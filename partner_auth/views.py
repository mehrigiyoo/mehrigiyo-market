from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.conf import settings
from .permissions import authenticate_partner
from client.models import ClientProfile
from datetime import date

UserModel = get_user_model()


class PartnerTokenSerializer(serializers.Serializer):
    """Partner token olish uchun serializer"""
    user_phone = serializers.CharField(required=True, help_text="Foydalanuvchi telefon raqami")

    # Ixtiyoriy: agar user yangi bo'lsa, qo'shimcha ma'lumotlar
    create_if_not_exists = serializers.BooleanField(default=False, help_text="Agar user yo'q bo'lsa, yangi yaratish")

    # User yaratish uchun ma'lumotlar (create_if_not_exists=True bo'lsa)
    full_name = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female')],
        required=False
    )
    age = serializers.IntegerField(min_value=1, max_value=120, required=False)

    def validate(self, attrs):
        # Agar create_if_not_exists=True bo'lsa, kerakli fieldlar tekshirish
        if attrs.get('create_if_not_exists', False):
            if not attrs.get('full_name'):
                raise serializers.ValidationError({
                    "full_name": "create_if_not_exists=True bo'lganda full_name majburiy"
                })
            if not attrs.get('gender'):
                raise serializers.ValidationError({
                    "gender": "create_if_not_exists=True bo'lganda gender majburiy"
                })
            if not attrs.get('age'):
                raise serializers.ValidationError({
                    "age": "create_if_not_exists=True bo'lganda age majburiy"
                })

        return attrs


class PartnerTokenView(APIView):
    """
    Partner ilovalar uchun token olish endpoint

    Bu endpoint orqali hamkor ilovalar o'z foydalanuvchilari uchun
    JWT token olishlari mumkin.

    Headers:
        X-API-Key: Partner API key
        X-API-Secret: Partner API secret

    Body:
        user_phone: Foydalanuvchi telefon raqami
        create_if_not_exists: true/false (default: false)
        full_name: Ism (create_if_not_exists=true bo'lsa)
        gender: male/female (create_if_not_exists=true bo'lsa)
        age: Yosh (create_if_not_exists=true bo'lsa)

    Response:
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "expires_in": 3600,
            "token_type": "Bearer",
            "user": {
                "phone": "+998901234567",
                "is_new_user": false
            }
        }
    """

    @authenticate_partner
    def post(self, request):
        serializer = PartnerTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_phone = serializer.validated_data['user_phone']
        create_if_not_exists = serializer.validated_data.get('create_if_not_exists', False)

        # Telefon raqamini normalize qilish (sizning normalize_phone funksiyangiz)
        from config.validators import normalize_phone  # O'zingizning utils'dan import qiling
        user_phone = normalize_phone(user_phone)

        # User ni topish yoki yaratish
        user = None
        is_new_user = False

        try:
            user = UserModel.objects.get(phone=user_phone)
        except UserModel.DoesNotExist:
            if create_if_not_exists:
                # Yangi user yaratish
                user = self._create_user(
                    phone=user_phone,
                    full_name=serializer.validated_data.get('full_name'),
                    gender=serializer.validated_data.get('gender'),
                    age=serializer.validated_data.get('age'),
                    partner=request.partner
                )
                is_new_user = True

                # Partner statistikasini yangilash
                request.partner.total_users_created += 1
                request.partner.save(update_fields=['total_users_created'])
            else:
                return Response(
                    {
                        "detail": "Foydalanuvchi topilmadi",
                        "user_phone": user_phone,
                        "hint": "create_if_not_exists=true qilib yuborishingiz mumkin"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        # User faol emasligini tekshirish
        if not user.is_active:
            return Response(
                {"detail": "Foydalanuvchi aktiv emas"},
                status=status.HTTP_403_FORBIDDEN
            )

        # JWT token yaratish
        refresh = RefreshToken.for_user(user)

        # Qo'shimcha claims qo'shish (ixtiyoriy)
        refresh['partner_id'] = request.partner.id
        refresh['partner_name'] = request.partner.name

        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "expires_in": int(settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(hours=24)).total_seconds()),
            "token_type": "Bearer",
            "user": {
                "phone": user.phone,
                "role": user.role,
                "is_new_user": is_new_user
            }
        }, status=status.HTTP_200_OK)

    def _create_user(self, phone, full_name, gender, age, partner):
        """Yangi user yaratish (partner orqali)"""

        # Random parol yaratish
        from django.utils.crypto import get_random_string
        random_password = get_random_string(32)

        # User yaratish
        user = UserModel.objects.create_user(
            phone=phone,
            password=random_password,
            role=UserModel.Roles.CLIENT,
            is_active=True  # Partner orqali kelgan userlar darhol active
        )

        # Client profile yaratish
        birthday = date.today().replace(year=date.today().year - age)

        ClientProfile.objects.create(
            user=user,
            full_name=full_name,
            gender=gender,
            birthday=birthday
        )

        return user


class PartnerRefreshTokenView(APIView):
    """
    Partner uchun refresh token endpoint

    Headers:
        X-API-Key: Partner API key
        X-API-Secret: Partner API secret

    Body:
        refresh_token: Refresh token
    """

    @authenticate_partner
    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response(
                {"detail": "refresh_token majburiy"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)

            return Response({
                "access_token": str(refresh.access_token),
                "expires_in": int(
                    settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(hours=24)).total_seconds()),
                "token_type": "Bearer"
            })
        except Exception as e:
            return Response(
                {"detail": "Noto'g'ri yoki muddati o'tgan refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )