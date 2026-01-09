from random import randrange

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from config.helpers import send_sms_code, validate_sms_code
from config.responses import ResponseFail, ResponseSuccess
from paymeuz.models import PaymeTransactionModel
from shop.models import Medicine
from shop.serializers import MedicineSerializer
from specialist.models import Doctor
from specialist.serializers import DoctorSerializer
from .models import Referrals, UserModel, CountyModel, RegionModel, DeliveryAddress, SmsCode
from .serializers import (CheckPhoneNumberSerializer, SmsSerializer, ConfirmSmsSerializer, RegistrationSerializer,
                          RegionSerializer, CountrySerializer, UserSerializer, DeliverAddressSerializer, PkSerializer,
                          OfferSerializer, ChangePasswordSerializer, ReferalUserSerializer)


from django.shortcuts import get_object_or_404
from django.db.models import Count
from django_filters import rest_framework as filters
from rest_framework import filters as rest_filters


class SendSmsThrottle(SimpleRateThrottle):
    scope = "send_sms"

    def get_cache_key(self, request, view):
        return "send_sms"


class DeleteUserProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='delete_user_profile',
        operation_description="delete_user_profile"
    )
    def post(self, request):
        phone_number = request.data['phone_number']

        user = UserModel.objects.get(username=phone_number)
        self_user = request.user

        if user.id == self_user.id:
            user.username += f"_deleted_{randrange(1000, 9999)}"
            user.is_active = False
            user.save()

            # user.delete()
            return ResponseSuccess(data="Successfully deleted", request=request.method)

        return ResponseFail(data="User not found or not match", request=request.method)


class CheckPhoneNumberView(APIView):
    @swagger_auto_schema(
        operation_id='check_phone_number',
        operation_description="check_phone_number",
        request_body=CheckPhoneNumberSerializer(),
        responses={
            '200': CheckPhoneNumberSerializer()
        }
    )
    def post(self, request):
        phone_number = request.data['phone']

        users = UserModel.objects.filter(username=phone_number)
        if len(users) >= 1:
            return ResponseSuccess(True, request=request.method)

        return ResponseSuccess(False, request=request.method)


class SendSmsView(APIView):
    throttle_classes = [SendSmsThrottle]

    @swagger_auto_schema(
        operation_id='send_sms',
        operation_description="send_sms",
        request_body=SmsSerializer(),
        responses={
            '200': SmsSerializer()
        },
        manual_parameters=[
            openapi.Parameter('link', openapi.IN_QUERY, description="for link",
                              type=openapi.TYPE_BOOLEAN)
        ],
    )
    def post(self, request):
        link = request.GET.get('link', False)

        serializer = SmsSerializer(data=request.data)
        if serializer.is_valid():
            send_sms_code(request, serializer.data['phone'], link, serializer.data['signature'])
            return ResponseSuccess(request=request.method)
        return ResponseFail(data=serializer.errors, request=request.method)


class ConfirmSmsView(APIView):
    @swagger_auto_schema(
        operation_id='send_sms_confirm',
        operation_description="send_sms_confirm",
        request_body=ConfirmSmsSerializer(),
        responses={
            '200': ConfirmSmsSerializer()
        },
    )
    def post(self, request):
        serializer = ConfirmSmsSerializer(data=request.data)
        if serializer.is_valid():
            if validate_sms_code(serializer.data['phone'], serializer.data['code']):
                return ResponseSuccess(data="Telefon nomer tasdiqlandi", request=request.method)
            else:
                return ResponseFail(data='Code hato kiritilgan', request=request.method)
        return ResponseFail(data=serializer.errors, request=request.method)


# @DEPRECATED
# class ForgotPasswordView(APIView):
#     @swagger_auto_schema(
#         operation_id='forget-password',
#         operation_description='forget password'
#     )
#     def post(self, request):
#         phone_number = request.data['username']
#
#         try:
#             user_model = UserModel.objects.get(username=phone_number)
#         except:
#             return ResponseFail(data={}, request=request.method)
#
#         return ResponseSuccess(data={"s": "ok"}, request=request.method)
#
#     @swagger_auto_schema(
#         operation_id='reset-password',
#         operation_description='Reset password',
#     )
#     def put(self, request):
#         pass

class OauthRegisterView(APIView):
    def get():
        return ResponseSuccess(data=[])

    def post(self, request):
        pass


class RegistrationView(APIView):

    # def get(self, request):
    #     serializer = RegistrationSerializer()
    #     return ResponseSuccess(data=serializer.data, request=request.method)
    @swagger_auto_schema(
        operation_id='registration',
        operation_description="registration",
        request_body=RegistrationSerializer(),
        responses={
            '200': RegistrationSerializer()
        },
    )
    def post(self, request):
        number = request.data['username']
        inviter = request.data['invited']
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            numbers = SmsCode.objects.filter(confirmed=True)
            access = False
            for i in numbers:
                if number == i.phone:
                    access = True
                    i.confirmed = False
                    i.save()

            if access:
                user = serializer.save()

                # TODO: make transactions!!!

                if inviter and inviter is not None:
                    inviter_user = UserModel.objects.filter(username=inviter).exists()

                    if inviter_user:
                        inviter_user = UserModel.objects.get(username=inviter)
                        try:
                            Referrals.objects.create(
                                user=inviter_user,
                                invited_user=user.username
                            )

                            PaymeTransactionModel.objects.create(
                                request_id=inviter,
                                order_id=number,
                                phone=user.username,
                                amount=10000 * 100,
                                status='processing',
                                _type='referal',
                            )

                        except:
                            user.delete()

                access_token = AccessToken().for_user(user)
                refresh_token = RefreshToken().for_user(user)

                return ResponseSuccess(data=dict({
                    "refresh": str(refresh_token),
                    "access": str(access_token)
                }), request=request.method)
            else:
                return ResponseFail(data='Ushbu raqam sms tekshiruvidan o\'tmagan', request=request.method)
        else:
            return ResponseFail(data=serializer.errors, request=request.method)


class ChangePassword(APIView):
    @swagger_auto_schema(
        operation_id='change_password',
        operation_description="Password change",
        request_body=ChangePasswordSerializer(),
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            numbers = SmsCode.objects.filter(confirmed=True)
            access = False
            for i in numbers:
                if serializer.data['phone'] == i.phone:
                    access = True
                    i.confirmed = False
                    i.save()
            if access:
                user = UserModel.objects.get(username=serializer.data['phone'])
                user.set_password(serializer.data['new_password'])
                user.save()
                return ResponseSuccess()
            else:
                return ResponseFail(data='Ushbu raqam sms tekshiruvidan o\'tmagan')
        else:
            return ResponseFail(data=serializer.errors)


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
    permission_classes = (IsAuthenticated,)

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


class AddAddressView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="Region_id",
                              type=openapi.TYPE_NUMBER)
        ], operation_description='')
    @action(detail=False, methods=['post'])
    def post(self, request):
        key = request.GET.get('pk', False)
        if key:
            region = RegionModel.objects.get(id=key)
            user = request.user
            user.address = region
            user.save()
            return ResponseSuccess(request=request.method)
        return ResponseFail(data='Bunday Viloyat mavjud emas', request=request.method)

    @swagger_auto_schema(
        request_body=RegionSerializer(),
    )
    @action(detail=False, methods=['put'])
    def put(self, request):
        reg = RegionModel.objects.get(id=request.GET['id'])
        ser = RegionSerializer(reg, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return ResponseSuccess(ser.data)
        else:
            return ResponseFail(data=ser.errors)

    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="Delivery address",
                              type=openapi.TYPE_NUMBER)
        ], operation_description='')
    @action(detail=False, methods=['delete'])
    def delete(self, request):
        key = request.GET.get('pk', False)
        if key:
            DeliveryAddress.objects.get(id=key).delete()

            return ResponseSuccess(request=request.method)
        return ResponseFail(data='Bunday Delivery address mavjud emas', request=request.method)


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


class DoctorView(generics.ListAPIView, APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DoctorSerializer

    @swagger_auto_schema(
        operation_id='get_favorite_doctors',
        operation_description="get_favorite_doctors",
        # request_body=UserSerializer(),
        responses={
            '200': DoctorSerializer()
        },
    )
    def get(self, request, *args, **kwargs):
        self.queryset = request.user.favorite_doctor.all()
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='add_favorite_doctor',
        operation_description="add_favorite_doctor",
        request_body=PkSerializer(),
        # responses={
        #     '200': MedicineSerializer()
        # },
    )
    def post(self, request):
        try:
            doc = Doctor.objects.get(id=request.data['pk'])
        except:
            return ResponseFail(data='Bunday doktr mavjud emas', request=request.method)
        user = request.user
        user.favorite_doctor.add(doc)
        user.save()
        return ResponseSuccess(request=request.method)

    @swagger_auto_schema(
        operation_id='remove_favorite_doctor',
        operation_description="add_favorite_doctor",
        request_body=PkSerializer(),
        # responses={
        #     '200': MedicineSerializer()
        # },
    )
    def delete(self, request):
        try:
            doc = Doctor.objects.get(id=request.data['pk'])
        except:
            return ResponseFail(data='Bunday doktor mavjud emas', request=request.method)
        user = request.user
        user.favorite_doctor.remove(doc)
        user.save()
        return ResponseSuccess(request=request.method)


class DeliverAddressView(generics.ListAPIView, APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeliverAddressSerializer

    @swagger_auto_schema(
        operation_id='get_delivery_address',
        operation_description="get_delivery_address",
        # request_body=UserSerializer(),
        responses={
            '200': DeliverAddressSerializer()
        },
    )
    def get(self, request, *args, **kwargs):
        self.queryset = DeliveryAddress.objects.filter(user=request.user)
        return self.list(request, *args, **kwargs)

    # def get(self, request):
    #     address = DeliveryAddress.objects.filter(user=request.user)
    #     serializers = DeliverAddressSerializer(address, many=True)
    #     return ResponseSuccess(data=serializers.data, request=request.method)

    @swagger_auto_schema(
        operation_id='add_delivery_address',
        operation_description="add_delivery_address",
        request_body=DeliverAddressSerializer(),
        responses={
            '200': DeliverAddressSerializer()
        },
    )
    def post(self, request):
        region = RegionModel.objects.get(id=request.data["region"])
        serializers = DeliverAddressSerializer(data=request.data)
        del request.data["region"]
        if serializers.is_valid():
            da = DeliveryAddress(**serializers.data)
            da.user = request.user
            da.region = region
            da.save()
            serializers = DeliverAddressSerializer(da)
            return ResponseSuccess(data=serializers.data, request=request.method)
        else:
            return ResponseFail(data=serializers.errors, request=request.method)

    @swagger_auto_schema(
        operation_id='update_delivery_address',
        operation_description="update_delivery_address",
        request_body=DeliverAddressSerializer(),
        responses={
            '200': DeliverAddressSerializer()
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="Delivery address Id",
                              type=openapi.TYPE_NUMBER)
        ]
    )
    def put(self, request):
        key = request.GET.get('pk', False)
        add = DeliveryAddress.objects.get(id=key)
        try:
            region = RegionModel.objects.get(id=request.data["region"])
            add.region = region
        except:
            pass
        del request.data["region"]
        serializers = DeliverAddressSerializer(add, data=request.data, partial=True)
        if serializers.is_valid():
            serializers.save()
            return ResponseSuccess(data=serializers.data)
        else:
            return ResponseFail(data=serializers.errors)

    @swagger_auto_schema(
        operation_id='delete_delivery_address',
        operation_description="delete_delivery_address",
        request_body=PkSerializer(),
    )
    def delete(self, request):
        try:
            DeliveryAddress.objects.get(id=request.data["pk"]).delete()
            return ResponseSuccess(data='delete!')
        except:
            return ResponseFail(data='delivery address not found')


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
            'username': ['exact', 'icontains'],
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
    ordering_fields = ['username', 'email', 'is_active']
    ordering = ['username',]


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






