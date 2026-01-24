from django.contrib.auth import authenticate
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
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
from .models import UserModel, CountyModel, RegionModel, SmsCode
from .serializers import (SmsSerializer, ConfirmSmsSerializer,
                          RegionSerializer, CountrySerializer, UserSerializer, PkSerializer,
                          OfferSerializer, ChangePasswordSerializer, ReferalUserSerializer, UserAvatarSerializer,
                          PhoneCheckSerializer, ResetPasswordSerializer,
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
            purpose=SmsCode.Purpose.RESET_PASSWORD,
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




class UserView(generics.ListAPIView, generics.UpdateAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='get_user',
        operation_description="my data",
        # request_body=RegistrationSerializer(),
        responses={
            '200': UserSerializer()
        },
    )
    def get(self, request, *args, **kwargs):
        self.queryset = UserModel.objects.filter(id=request.user.id)
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='update_user',
        operation_description="update my data",
        request_body=UserSerializer(),
        responses={
            '200': UserSerializer()
        },
    )
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return ResponseSuccess(data=serializer.data, request=request.method)
        else:
            return ResponseFail(data=serializer.errors, request=request.method)


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


class MedicineView(generics.ListAPIView, APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MedicineSerializer

    @swagger_auto_schema(
        operation_id='get_favorite_medicines',
        operation_description="get_favorite_medicines",
        # request_body=UserSerializer(),
        responses={
            '200': MedicineSerializer()
        },
    )
    def get(self, request, *args, **kwargs):
        self.queryset = request.user.favorite_medicine.all()
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='add_favorite_medicines',
        operation_description="add_favorite_medicines",
        request_body=PkSerializer(),
        responses={
            '200': MedicineSerializer()
        },
    )
    def post(self, request):
        try:
            med = Medicine.objects.get(id=request.data['pk'])
        except:
            return ResponseFail(data='Bunday dori mavjud emas', request=request.method)
        user = request.user
        user.favorite_medicine.add(med)
        user.save()
        return ResponseSuccess(request=request.method)

    @swagger_auto_schema(
        operation_id='remove_favorite_medicines',
        operation_description="remove_favorite_medicines",
        request_body=PkSerializer(),
        # responses={
        #     '200': MedicineSerializer()
        # },
    )
    def delete(self, request):
        try:
            med = Medicine.objects.get(id=request.data['pk'])
        except:
            return ResponseFail(data='Bunday dori mavjud emas', request=request.method)
        user = request.user
        user.favorite_medicine.remove(med)
        user.save()
        return ResponseSuccess(request=request.method)


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






