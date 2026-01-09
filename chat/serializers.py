from random import random
from rest_framework import serializers

from chat.keywords import APP_CERTIFICATE, APP_ID
from .models import ChatRoom, Message, FileMessage
from account.models import UserModel
from specialist.models import AdviceTime
from specialist.serializers import AdviceSerializer
from vendor.AgoraDynamicKey import RtcTokenBuilder2

import datetime


class ChatSerializer(serializers.ModelSerializer):
    # messages = MessageSerializer(many=True)

    app_id = serializers.SerializerMethodField(method_name="get_app_id")
    channel_name = serializers.SerializerMethodField(method_name="generate_channel_name")
    token = serializers.SerializerMethodField(method_name="generate_chat_token")

    def get_app_id(self, _: ChatRoom):
        return APP_ID

    def generate_channel_name(self, chat_room: ChatRoom):
        return f"chat_{chat_room.client.username}|{chat_room.doktor.username}-{chat_room.pk}"

    def generate_chat_token(self, chat_room: ChatRoom):
        channel_name = f"chat_{chat_room.client.username}|{chat_room.doktor.username}-{chat_room.pk}"
        expirationTime = datetime.datetime.now().timestamp() / 1000 + 3600
        token = RtcTokenBuilder2.RtcTokenBuilder.build_token_with_uid(
            APP_ID,
            APP_CERTIFICATE,
            channel_name,
            0, 2,
            expirationTime,
            expirationTime)

        return token

    class Meta:
        model = ChatRoom
        fields = ['id', 'get_doctor_fullname', 'get_client_fullname', 'app_id', 'channel_name', 'token', 'created_at']


class FileMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileMessage
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    file_message = serializers.SerializerMethodField()
    owner_avatar = serializers.ImageField(source='owner.avatar', read_only=True)
    owner_first_name = serializers.CharField(source='owner.first_name', read_only=True)
    owner_last_name = serializers.CharField(source='owner.last_name', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'owner', 'text', 'file_message', 'created_at', 'owner_avatar', 'owner_first_name',
                  'owner_last_name']

    def get_file_message(self, obj):
        if obj.file_message:
            return FileMessageSerializer(obj.file_message).data
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = representation['owner']
        u = UserModel.objects.get(id=user)

        if u.is_staff:
            representation['doctor'] = True
        else:
            representation['doctor'] = False

        # User haqida qo'shimcha ma'lumotlarni qo'shish
        representation['owner_avatar'] = u.avatar.url if u.avatar else None
        representation['owner_first_name'] = u.first_name
        representation['owner_last_name'] = u.last_name

        return representation



# class MessageSerializer(serializers.ModelSerializer):
#     file_message = FileMessageSerializer()
#
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         user = representation['owner']
#         u = UserModel.objects.get(id=user)
#
#         if u.is_staff:
#             representation['doctor'] = True
#         else:
#             representation['doctor'] = False
#
#         return representation
#
#     class Meta:
#         model = Message
#         fields = '__all__'


class RoomsSerializer(serializers.ModelSerializer):
    last_message = MessageSerializer()
    doktor = serializers.SerializerMethodField(method_name='get_doctor')
    client = serializers.SerializerMethodField(method_name='get_client')
    receiver = serializers.SerializerMethodField(method_name='get_receiver')
    user_type = serializers.SerializerMethodField(method_name='get_user_type')
    advice_time = serializers.SerializerMethodField(method_name="get_advice")

    def get_receiver(self, obj):
        me = self.context.get('request').user

        if me.id != obj.client.id:
            return {
                "id": obj.client.id,
                "name": obj.client.get_full_name()
            }

        elif me.id != obj.doktor.id:
            return {
                "id": obj.doktor.id,
                "name": obj.doktor.get_full_name()
            }

        return {}

    def get_advice(self, obj):
        ad = AdviceTime.objects.filter(doctor=obj.doktor.specialist_doctor,
                                       client=obj.client,
                                       start_time__gte=datetime.datetime.now()).first()
        if ad != None:
            ser = AdviceSerializer(ad)
            return ser.data
        else:
            return None

    def get_doctor(self, obj):
        try:
            imma = obj.doktor.specialist_doctor.image.url
            return {
                "id": obj.doktor.id,
                "doctor_account_id": obj.doktor.id,
                "specialist_account_id": obj.doktor.specialist_doctor.id,
                "name": obj.doktor.get_full_name(),
                "image": imma,
                "type": obj.doktor.specialist_doctor.type_doctor.name
            }
        except:
            return {
                "id": obj.doktor.id,
                "doctor_account_id": obj.doktor.id,
                "specialist_account_id": obj.doktor.specialist_doctor.id,
                "name": obj.doktor.get_full_name(),
                "type": obj.doktor.specialist_doctor.type_doctor.name
            }

    def get_user_type(self, obj):
        me = self.context.get('request').user
        return "doctor" if me.id == obj.doktor.id else "client"

    def get_client(self, obj):
        return {
            "id": obj.client.id,
            "name": obj.client.get_full_name(),
            "type": "doctor" if obj.client.is_staff == True else "client"
        }
        # return obj.client.get_full_name()

    class Meta:
        model = ChatRoom
        fields = (
            'id', 'user_type', 'receiver', 'client', 'doktor', 'last_message', 'advice_time', 'token', 'created_at')



class ChatRoomAndDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields =  [
            'id',
            'admin',
            'client',
            'doktor',
            'messages',
            'created_at'
        ]