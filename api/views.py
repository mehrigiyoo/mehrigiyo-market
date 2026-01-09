from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .serializers import *

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class UserModelAdminViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserModelAdminSerializer
    permission_classes = [IsAuthenticated, ]


class SmsCodeAdminViewSet(viewsets.ModelViewSet):
    queryset = SmsCode.objects.all()
    serializer_class = SmsCodeAdminSerializer
    permission_classes = [IsAuthenticated, ]


class SmsAttemptAdminViewSet(viewsets.ModelViewSet):
    queryset = SmsAttempt.objects.all()
    serializer_class = SmsAttemptAdminSerializer
    permission_classes = [IsAuthenticated, ]


class CountyModelAdminViewSet(viewsets.ModelViewSet):
    queryset = CountyModel.objects.all()
    serializer_class = CountryModelAdminSerializer
    permission_classes = [IsAuthenticated, ]


class RegionModelAdminViewSet(viewsets.ModelViewSet):
    queryset = RegionModel.objects.all()
    serializer_class = RegionModelAdminSerializer
    permission_classes = [IsAuthenticated, ]


class DeliveryAddressAdminViewSet(viewsets.ModelViewSet):
    queryset = DeliveryAddress.objects.all()
    serializer_class = DeliveryAddressAdminSerializer
    permission_classes = [IsAuthenticated, ]


class MessageAdminViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageAdminSerializer
    permission_classes = [IsAuthenticated, ]


class ChatRoomAdminViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomAdminSerializer
    permission_classes = [IsAuthenticated, ]


class CommentDoctorAdminViewSet(viewsets.ModelViewSet):
    queryset = CommentDoctor.objects.all()
    serializer_class = CommentDoctorAdminSerializer
    permission_classes = [IsAuthenticated, ]


class CommentMedicineAdminViewSet(viewsets.ModelViewSet):
    queryset = CommentMedicine.objects.all()
    serializer_class = CommentMedicineAdminSerializer
    permission_classes = [IsAuthenticated, ]


class NewsModelAdminViewSet(viewsets.ModelViewSet):
    queryset = NewsModel.objects.all()
    serializer_class = NewsModelAdminSerializer
    # permission_classes = [IsAuthenticated, ]


class PaymeTransactionModelAdminViewSet(viewsets.ModelViewSet):
    queryset = PaymeTransactionModel.objects.all()
    serializer_class = PaymeTransactionModelAdminSerializer
    permission_classes = [IsAuthenticated, ]


class CardAdminViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardAdminSerializer
    permission_classes = [IsAuthenticated, ]


class PicturesMedicineAdminViewSet(viewsets.ModelViewSet):
    queryset = PicturesMedicine.objects.all()
    serializer_class = PicturesMedicineAdminSerializer
    permission_classes = [IsAuthenticated, ]


class TypeMedicineAdminViewSet(viewsets.ModelViewSet):
    queryset = TypeMedicine.objects.all()
    serializer_class = TypeMedicineAdminSerializer
    permission_classes = [IsAuthenticated, ]


class MedicineAdminViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineAdminSerializer
    permission_classes = [IsAuthenticated, ]


class CartModelAdminViewSet(viewsets.ModelViewSet):
    queryset = CartModel.objects.all()
    serializer_class = CartModelAdminSerializer
    permission_classes = [IsAuthenticated, ]


class DeliveryManAdminViewSet(viewsets.ModelViewSet):
    queryset = DeliveryMan.objects.all()
    serializer_class = DeliveryManAdminSerializer
    # permission_classes = [IsAuthenticated, ]


class OrderModelAdminViewSet(viewsets.ModelViewSet):
    queryset = OrderModel.objects.all()
    serializer_class = OrderModelAdminSerializer
    permission_classes = [IsAuthenticated, ]


class TypeDoctorAdminViewSet(viewsets.ModelViewSet):
    queryset = TypeDoctor.objects.all()
    serializer_class = TypeDoctorAdminSerializer
    permission_classes = [IsAuthenticated, ]


class DoctorAdminViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorAdminSerializer
    # permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend, ]

    filterset_fields = ['type_doctor']

    # def get_queryset(self):
    #     request = self.request
    #
    #     type_doctor_param = request.GET.get('type_doctor')
    #     type_doctor = TypeDoctor.objects.filter(name=type_doctor_param)
    #
    #     if not type_doctor.exists():
    #         return Doctor.objects.all()
    #
    #     return Doctor.objects.filter(type_doctor=type_doctor)


class RateDoctorAdminViewSet(viewsets.ModelViewSet):
    queryset = RateDoctor.objects.all()
    serializer_class = RateDoctorAdminSerializer
    permission_classes = [IsAuthenticated, ]


class AdviceTimeAdminViewSet(viewsets.ModelViewSet):
    queryset = AdviceTime.objects.all()
    serializer_class = AdviceTimeAdminSerializer
    permission_classes = [IsAuthenticated, ]





class NotificationAdminViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationAdminSerializer
    # permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='list_notifications',
        operation_description="Get notifications",
        responses={
            '200': NotificationAdminSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='create_notification',
        operation_description="Create a new notification",
        responses={
            '201': NotificationAdminSerializer()
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='retrieve_notification',
        operation_description="Retrieve a specific notification",
        responses={
            '200': NotificationAdminSerializer()
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='update_notification',
        operation_description="Update an existing notification",
        responses={
            '200': NotificationAdminSerializer()
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='partial_update_notification',
        operation_description="Partially update an existing notification",
        responses={
            '200': NotificationAdminSerializer()
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='destroy_notification',
        operation_description="Delete a specific notification",
        responses={
            '204': 'No Content'
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='call_notification',
        operation_description="Post call notifications",
        responses={
            '200': 'Success',
            '400': 'Bad Request'
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="Send User ID", type=openapi.TYPE_NUMBER)
        ],
    )
    @action(detail=False, methods=['post'], url_path='call-notification')
    def call_notification(self, request):
        pk = request.GET.get('pk', False)
        if not pk:
            return Response({'message': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserModel.objects.get(id=pk)
        except UserModel.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        current_user = request.user
        image_path = None

        try:
            image_path = current_user.avatar.path
        except Exception as e:
            print(f"Error getting avatar path: {e}")

        res = sendPush(
            title='CALL',
            description=current_user.get_full_name(),
            registration_tokens=[user.notificationKey],
            image=image_path
        )

        success_count = res.success_count
        if success_count == 0:
            return Response({'message': f'Failed. Exceptions: {res.responses[0].exception}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Success!'}, status=status.HTTP_200_OK)
