from rest_framework import serializers

from account.models import UserModel, SmsCode, SmsAttempt, CountyModel, RegionModel, DeliveryAddress


class UserModelAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = '__all__'


class SmsCodeAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsCode
        fields = '__all__'


class SmsAttemptAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsAttempt
        fields = '__all__'


class CountryModelAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountyModel
        fields = '__all__'


class RegionModelAdminSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = RegionModel
        fields = '__all__'


class DeliveryAddressAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = '__all__'


from chat.models import Message, ChatRoom


class MessageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class ChatRoomAdminSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'admin',
            'doktor',
            'client',
            'token',
            'created_at',
            'last_message',
            'receiver',
            'thread_id'
        ]

    def get_last_message(self, obj):
        last_message = obj.last_message()
        if last_message:
            return {
                'id': last_message.id,
                'file_message': {
                    'id': last_message.file_message.id if last_message.file_message else None,
                    'file': last_message.file_message.file.url if last_message.file_message and last_message.file_message.file else None,
                    'image': last_message.file_message.image.url if last_message.file_message and last_message.file_message.image else None,
                    'size': last_message.file_message.size,
                    'video': last_message.file_message.video
                } if last_message.file_message else None,
                'text': last_message.text,
                'created_at': last_message.created_at,
                'owner': last_message.owner.id,
                'doctor': last_message.owner.is_staff
            }
        return None

    def get_receiver(self, obj):
        last_message = obj.last_message()
        if last_message:
            sender = last_message.owner
            receivers = []
            if obj.doktor and obj.doktor != sender:
                receivers.append({
                    'id': obj.doktor.id,
                    'name': obj.get_doctor_fullname(),
                })
            if obj.client and obj.client != sender:
                receivers.append({
                    'id': obj.client.id,
                    'name': obj.get_client_fullname(),
                })
            if obj.admin and obj.admin != sender:
                receivers.append({
                    'id': obj.admin.id,
                    'name': obj.admin.get_full_name(),
                })
            return receivers
        return None

    def to_representation(self, instance):
        if instance.doktor:
            user_type = 'doctor'
        elif instance.client:
            user_type = 'client'
        else:
            user_type = 'admin'

        doctor_chat = instance.doktor
        doctor_user = doctor_chat.doctor if doctor_chat and hasattr(doctor_chat, 'doctor') else None
        specialist_user = doctor_chat.specialist_doctor if doctor_chat and hasattr(doctor_chat,
                                                                                   'specialist_doctor') else None

        # If either doctor_user or specialist_user exists, determine type_user
        user = doctor_user or specialist_user
        d_type = user.type_doctor if user and hasattr(user, 'type_doctor') else None
        doctor_type = d_type.name if d_type else None

        result = {
            'id': instance.id,
            'user_type': user_type,
            'receiver': self.get_receiver(instance),
            'client': {
                'id': instance.client.id if instance.client else None,
                'name': instance.get_client_fullname() if instance.client else None,
            },
            'doctor': {
                'id': instance.doktor.id if instance.doktor else None,
                'doctor_account_id': instance.doktor.id if instance.doktor else None,
                'specialist_account_id': instance.doktor.specialist_doctor.id if instance.doktor and instance.doktor.specialist_doctor else None,
                'name': instance.get_doctor_fullname() if instance.doktor else None,
                'image': instance.doktor.avatar.url if instance.doktor and instance.doktor.avatar else None,
                'type': doctor_type,
            },
            'last_message': self.get_last_message(instance),
            'token': instance.token,
            'created_at': instance.created_at
        }
        return result
# class ChatRoomAdminSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ChatRoom
#         fields = '__all__'


from comment.models import CommentDoctor, CommentMedicine


class CommentDoctorAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentDoctor
        fields = '__all__'


class CommentMedicineAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentMedicine
        fields = '__all__'


from news.models import NewsModel, Notification


class NewsModelAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsModel
        fields = '__all__'


from paymeuz.models import PaymeTransactionModel, Card


class PaymeTransactionModelAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymeTransactionModel
        fields = '__all__'


class CardAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'


from shop.models import PicturesMedicine, TypeMedicine, Medicine, CartModel, DeliveryMan, OrderModel


class PicturesMedicineAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = PicturesMedicine
        fields = '__all__'


class TypeMedicineAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeMedicine
        fields = '__all__'


class MedicineAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'


class CartModelAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartModel
        fields = '__all__'


class DeliveryManAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryMan
        fields = '__all__'


class OrderModelAdminSerializer(serializers.ModelSerializer):
    user = UserModelAdminSerializer()

    class Meta:
        model = OrderModel
        fields = '__all__'


from specialist.models import TypeDoctor, Doctor, RateDoctor, AdviceTime


class TypeDoctorAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeDoctor
        fields = '__all__'


class DoctorAdminSerializer(serializers.ModelSerializer):
    type_doctor = serializers.SerializerMethodField(method_name="get_type_doctor")

    def get_type_doctor(self, instance: Doctor):
        if instance.type_doctor is None:
            return {}

        return {
            "id": instance.type_doctor.id,
            "name": instance.type_doctor.name
        }

    class Meta:
        model = Doctor
        fields = '__all__'


class RateDoctorAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateDoctor
        fields = '__all__'


class AdviceTimeAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdviceTime
        fields = '__all__'



class NotificationAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
