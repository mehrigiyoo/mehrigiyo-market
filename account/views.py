from django.contrib.auth import authenticate
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from config.helpers import send_sms_code
from config.responses import ResponseFail, ResponseSuccess
from config.validators import normalize_phone
from shop.models import Medicine
from shop.serializers import MedicineSerializer
from .models import UserModel, CountyModel, RegionModel, SmsCode, UserDevice
from .serializers import (SmsSerializer, ConfirmSmsSerializer,
                          RegionSerializer, CountrySerializer, UserSerializer, PkSerializer,
                          OfferSerializer, ChangePasswordSerializer, ReferalUserSerializer, UserAvatarSerializer,
                          PhoneCheckSerializer, ResetPasswordSerializer, LogoutSerializer, DeleteAccountSerializer,
                          UserDeviceSerializer,
                          )


from django.shortcuts import get_object_or_404
from django.db.models import Count
from django_filters import rest_framework as filters
from rest_framework import filters as rest_filters
now = timezone.now()

class SendSmsThrottle(SimpleRateThrottle):
    scope = "send_sms"

    def get_cache_key(self, request, view):
        return "send_sms"

class LoginView(APIView):
    def post(self, request):
        phone = request.data.get("phone")
        password = request.data.get("password")

        user = authenticate(request, phone=phone, password=password)
        if not user:
            return Response({"detail": "No active account found with the given credentials"}, status=401)

        # Doctor tasdiqlanishini tekshirish
        if user.role == UserModel.Roles.DOCTOR and not user.is_approved:
            return Response({"detail": "Profilingiz admin tomonidan tasdiqlanmagan"}, status=403)

        # Client, operator yoki tasdiqlangan doctor
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": user.role,
            "is_approved": user.is_approved
        })

class UserAvatarUpdateView(UpdateAPIView):
    serializer_class = UserAvatarSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class PhoneCheckAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PhoneCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']

        # Faqat client rolidagi userlarni tekshiramiz
        exists = UserModel.objects.filter(phone=phone, role='client').exists()

        if exists:
            return Response({
                "exists": True,
                "message": "Client exists. Proceed to login."
            })
        else:
            return Response({
                "exists": False,
                "message": "Client not found. Proceed to register."
            })


class SendSmsView(APIView):
    def post(self, request):
        serializer = SmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = normalize_phone(serializer.validated_data['phone'])
        purpose = serializer.validated_data['purpose']

        send_sms_code(
            request=request,
            phone=phone,
            purpose=purpose
        )

        return ResponseSuccess(
            data={
                "message": "SMS yuborildi",
                "purpose": purpose
            },
            request=request.method
        )


class ConfirmSmsView(APIView):
    def post(self, request):
        serializer = ConfirmSmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = normalize_phone(serializer.validated_data['phone'])
        code = serializer.validated_data['code']
        purpose = serializer.validated_data['purpose']

        sms = SmsCode.objects.filter(
            phone=phone,
            code=code,
            purpose=purpose,
            confirmed=False,
            expire_at__gte=timezone.now()
        ).first()

        if not sms:
            return ResponseFail(
                data="Kod noto‘g‘ri, eskirgan yoki allaqachon ishlatilgan",
                request=request.method
            )

        # Kodni tasdiqlaymiz
        sms.confirmed = True
        sms.save(update_fields=['confirmed'])

        return ResponseSuccess(
            data={
                "message": "SMS muvaffaqiyatli tasdiqlandi",
                "purpose": purpose
            },
            request=request.method
        )


class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"detail": "Eski parol noto‘g‘ri"},
                status=400
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {"detail": "Parol muvaffaqiyatli o‘zgartirildi"},
            status=200
        )


class ResetPasswordAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = normalize_phone(serializer.validated_data['phone'])

        sms = SmsCode.objects.filter(
            phone=phone,
            purpose='reset_password',
            confirmed=True,
            expire_at__gt=timezone.now()
        ).order_by('-created_at').first()

        if not sms:
            return Response(
                {"detail": "SMS tasdiqlanmagan yoki eskirgan"},
                status=400
            )

        try:
            user = UserModel.objects.get(phone=phone)
        except UserModel.DoesNotExist:
            return Response({"detail": "User topilmadi"}, status=404)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # one-time
        sms.delete()

        return Response(
            {"detail": "Parol tiklandi"},
            status=200
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "Logout successful"},
            status=status.HTTP_205_RESET_CONTENT
        )



class DeleteAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        password = serializer.validated_data['password']

        if not user.check_password(password):
            return Response(
                {"detail": "Password noto‘g‘ri"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete (senior approach)
        user.is_active = False
        user.deleted_at = timezone.now()  # agar field bo‘lsa
        user.save(update_fields=["is_active", "deleted_at"])

        # Tokenlarni ham o‘ldiramiz
        from rest_framework_simplejwt.tokens import OutstandingToken, BlacklistedToken

        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        return Response(
            {"detail": "Account muvaffaqiyatli o‘chirildi"},
            status=status.HTTP_200_OK
        )




class RegionView(APIView):
    # permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="country_id",
                              type=openapi.TYPE_NUMBER)
        ], operation_description='')
    @action(detail=False, methods=['get'])
    def get(self, request):
        key = request.GET.get('pk', False)
        if key:
            reg = RegionModel.objects.filter(country_id=key)
            serializer = RegionSerializer(reg, many=True)
            return ResponseSuccess(data=serializer.data, request=request.method)
        else:
            return ResponseFail(data='country_id is not send ')


class CountryView(APIView):
    # permission_classes = (IsAuthenticated,)
    @swagger_auto_schema(
        operation_id='get_country',
        operation_description="get countries",
        # request_body=UserSerializer(),
        responses={
            '200': CountrySerializer()
        },
    )
    def get(self, request):
        coun = CountyModel.objects.all().order_by('order_number')
        serializer = CountrySerializer(coun, many=True)
        return ResponseSuccess(data=serializer.data, request=request.method)


class OfferView(APIView):
    @swagger_auto_schema(
        operation_id='create_offer',
        operation_description="Create Offer",
        request_body=OfferSerializer(),
        responses={
            '200': OfferSerializer()
        },
    )
    def post(self, request):
        serializer = OfferSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseSuccess(data=serializer.data)
        else:
            return ResponseFail(data=serializer.errors)


class SetNotificationKeyView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='set_notification_key',
        operation_description="Set Notification Registration Key",
        request_body=openapi.Schema(
            required="key",
            type=openapi.TYPE_OBJECT,
            properties={
                'key': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
    )
    def post(self, request):
        key = request.data['key']

        if key:
            user = request.user
            user.notificationKey = key
            user.save()
            return ResponseSuccess(data="Notification key successfully set", request=request.method)

        return ResponseFail(data="Error while set notification key")


class SetRegistrationKeyView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='registration_key',
        operation_description="Set Registration key",
        # request_body=OfferSerializer(),
        # responses={
        #     '200': OfferSerializer()
        # },
        manual_parameters=[
            openapi.Parameter('regId', openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request):
        key = request.GET.get('regId', False)
        if key:
            user = request.user
            user.notificationKey = key
            user.save()
            return ResponseSuccess()
        return ResponseFail()




# Userlarni admin uchun listi
class UserFilterAPI(filters.FilterSet):
    class Meta:
        model = UserModel
        fields = {
            'phone': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'is_active': ['exact'],
            'last_name': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains']
        }

class UserForAdminViewAPI(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    filter_backends = (filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    filterset_class = UserFilterAPI
    ordering_fields = ['phone', 'email', 'is_active']
    ordering = ['phone',]


    def get_queryset(self):
        return UserModel.objects.filter(is_staff=False)


class ReferalUserForAdminViewAPI(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReferalUserSerializer

    def get_queryset(self):
        return UserModel.objects.annotate(referral_count=Count('referrals')).filter(is_staff=False)

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        action = request.data.get('action')
        user = get_object_or_404(UserModel, id=user_id)

        if action == 'block':
            user.is_active = False
        elif action == 'unblock':
            user.is_active = True
        user.save()

        return Response({'status': 'success', 'action': action})


class UserDeviceViewSet(viewsets.ModelViewSet):
    """
    User Device Management

    Endpoints:
    - POST   /api/devices/          - Register device
    - GET    /api/devices/          - List my devices
    - DELETE /api/devices/{id}/     - Remove device
    - POST   /api/devices/{id}/deactivate/ - Deactivate device
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserDeviceSerializer

    def get_queryset(self):
        """Get current user's devices"""
        return UserDevice.objects.filter(user=self.request.user)

    def create(self, request):
        """
        Register/Update device

        POST /api/devices/
        {
            "fcm_token": "eyJhbGc...",
            "device_id": "unique_device_id_123",
            "device_type": "android",
            "device_name": "Samsung Galaxy S21"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create or update
        device = serializer.save()

        # Mark device as active
        device.is_active = True
        device.save()

        return Response(
            UserDeviceSerializer(device).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, pk=None):
        """Delete device"""
        device = self.get_object()
        device.delete()

        return Response(
            {'message': 'Device removed'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate device (stop receiving notifications)

        POST /api/devices/{id}/deactivate/
        """
        device = self.get_object()
        device.is_active = False
        device.save()

        return Response({'message': 'Device deactivated'})
