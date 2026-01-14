import json

import requests
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from rest_framework.utils.serializer_helpers import ReturnDict

from account.models import UserModel
from paymeuz.keywords import TELEGRAM_CHAT_GROUP_ID, TG_SEND_MESSAGE, TG_SEND_VIDEO, TELEGRAM_PAYLOAD_URL, TG_SEND_FILE, \
    TG_SEND_PHOTO
from .models import ChatRoom, Message, FileMessage
from .serializers import MessageSerializer


def getReceiver(receiver_id):
    try:
        user = UserModel.objects.get(id=receiver_id)
    except:
        return False

    return user



def getMessage(chat_id, user, msg):
    """
    msg string yoki dict bo'lishi mumkin (file_message bilan ham ishlaydi)
    """
    file_obj = None

    # file_message borligini tekshirish
    if isinstance(msg, dict) and msg.get('file_message'):
        try:
            file_obj = FileMessage.objects.get(id=msg['file_message'])
            del msg['file_message']
        except FileMessage.DoesNotExist:
            file_obj = None

    # Agar msg string bo'lsa, uni dict ga aylantiramiz
    if isinstance(msg, str):
        msg_data = {"message": msg}  # default maydon nomi `message` ekan
    elif isinstance(msg, dict):
        msg_data = msg
    else:
        raise ValueError("msg faqat string yoki dict bo'lishi mumkin")

    # Message yaratish
    message = Message.objects.create(
        owner=user,
        file_message=file_obj,
        **msg_data
    )

    # ChatRoom ga qo'shish
    try:
        room = ChatRoom.objects.get(id=chat_id)
        room.messages.add(message)
        room.save()
    except ChatRoom.DoesNotExist:
        print(f"ChatRoom {chat_id} mavjud emas")

    # Serializer orqali JSON qaytarish
    serializer = MessageSerializer(message)
    return serializer.data


# def getMessage(chat_id, user, msg):
#     try:
#         f = FileMessage.objects.get(id=msg['file_message'])
#         del msg['file_message']
#     except:
#         f = None
#     message = Message(**msg)
#     message.owner = user
#     message.file_message = f
#     message.save()
#     room = ChatRoom.objects.get(id=chat_id)
#     room.messages.add(message)
#     room.save()
#     serializer = MessageSerializer(message)
#
#     return serializer.data


def sendToTelegram(chat_id, room_id, __dict: ReturnDict):
    return_data = False

    msg = Message.objects.get(id=__dict['id'])
    room = ChatRoom.objects.get(id=chat_id)
    data = dict({"chat_id": TELEGRAM_CHAT_GROUP_ID})

    if room.thread_id is None:
        chat_room = ChatRoom.objects.get(id=chat_id)

        response = requests.post(url=TELEGRAM_PAYLOAD_URL + "/createForumTopic", json=dict({
            "chat_id": TELEGRAM_CHAT_GROUP_ID,
            "name": f"{chat_room.client.get_full_name()} - #{chat_room.doktor.get_full_name()}"
        })).json()

        thread_id = response['result']['message_thread_id']
        room.thread_id = thread_id
        room.save()

    data["parse_mode"] = "HTML"

    if msg.file_message is not None:
        if msg.file_message.video:
            data["video"] = msg.file_message.file.url
            data["caption"] = f"<b><i>{msg.owner.get_full_name()}</i></b>"
            data["message_thread_id"] = room.thread_id

            response = requests.post(url=TG_SEND_VIDEO, json=data).json()
            return_data = response['ok']

        elif msg.file_message.file is not None:
            data["document"] = msg.file_message.file.url
            data["caption"] = f"<b><i>{msg.owner.get_full_name()}</i></b>"
            data["message_thread_id"] = room.thread_id

            response = requests.post(url=TG_SEND_FILE, json=data).json()
            return_data = response['ok']

        else:
            data["photo"] = msg.file_message.image.url
            data["caption"] = f"<b><i>{msg.owner.get_full_name()}</i></b>"
            data["message_thread_id"] = room.thread_id

            response = requests.post(url=TG_SEND_PHOTO, json=data).json()
            return_data = response['ok']

    else:
        data["text"] = f"<b><i>{msg.owner.get_full_name()}</i>:</b>\n\n{msg.text}"
        data["message_thread_id"] = room.thread_id

        response = requests.post(url=TG_SEND_MESSAGE, json=data).json()
        return_data = response['ok']

    return return_data


@database_sync_to_async
def createVideoChat(chat_id, user):
    message = Message(video=True)
    message.owner = user
    message.save()
    room = ChatRoom.objects.get(id=chat_id)
    room.messages.add(message)
    room.save()
    serializer = MessageSerializer(message)

    return serializer.data


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'chat_%s' % self.room_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            self.send(text_data=json.dumps({
                "status": "error",
                "error": "Invalid JSON"
            }))
            return

        chat_id = text_data_json.get('chat_id')
        msg = text_data_json.get('message')
        current_user = self.scope.get("user")

        if not chat_id or not msg:
            self.send(text_data=json.dumps({
                "status": "error",
                "error": "chat_id va message maydoni kerak"
            }))
            return

        print(current_user, '==========')

        # getMessage funksiyasini chaqiramiz
        try:
            data = getMessage(chat_id, current_user, msg)
        except Exception as e:
            self.send(text_data=json.dumps({
                "status": "error",
                "error": str(e)
            }))
            return

        # Telegramga yuborish (agar kerak bo‘lsa)
        try:
            sendToTelegram(chat_id, self.scope['url_route']['kwargs']['room_id'], data)
        except Exception as e:
            print(f"Telegram send failed: {e}")

        # Room ga broadcast
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'data': data
            }
        )

    def chat_message(self, event):
        data = event['data']
        self.send(text_data=json.dumps({
            "status": "success",
            "data": data,
        }))


class EventsConsumer(WebsocketConsumer):
    def connect(self):
        # self.query_data = parse_qs(self.scope['query_string'].decode())

        self.room_name = self.scope['user'].id
        self.room_group_name = 'user_%s' % self.room_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        json_data = json.loads(text_data)
        action = json_data['action']

        if action == "call":
            receiver_id = json_data['receiver_id']

            caller = self.scope['user']
            receiver = getReceiver(receiver_id)

            if receiver is False:
                return async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'user_notfound',
                        'data': 'Receiver not found on the database'
                    }
                )

            response_data = {
                "caller": {
                    "id": caller.id,
                    "full_name": caller.get_full_name(),
                    "first_name": caller.first_name,
                    "last_name": caller.last_name
                },
                "receiver": {
                    "id": receiver.id,
                    "full_name": receiver.get_full_name(),
                    "first_name": receiver.first_name,
                    "last_name": receiver.last_name
                },
                "app_id": json_data['app_id'] or "",
                "channel_name": json_data['channel_name'] or "",
                "token": json_data['token'] or ""
            }

            async_to_sync(self.channel_layer.group_send)(
                'user_%s' % receiver_id,
                {
                    'type': 'chat_message',
                    'data': response_data
                }
            )

        elif action == "call_end":
            receiver_id = json_data['receiver_id']

            caller = self.scope['user']
            receiver = getReceiver(receiver_id)

            if receiver is False:
                return async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'user_notfound',
                        'data': 'Receiver not found on the database'
                    }
                )

            response_data = {
                "caller": {
                    "id": caller.id,
                    "full_name": caller.get_full_name(),
                    "first_name": caller.first_name,
                    "last_name": caller.last_name
                },
                "receiver": {
                    "id": receiver.id,
                    "full_name": receiver.get_full_name(),
                    "first_name": receiver.first_name,
                    "last_name": receiver.last_name
                },
                "app_id": json_data['app_id'] or "",
                "channel_name": json_data['channel_name'] or "",
                "token": json_data['token'] or ""
            }

            async_to_sync(self.channel_layer.group_send)(
                'user_%s' % receiver_id,
                {
                    'type': 'video_call_end',
                    'data': response_data
                }
            )

    def chat_message(self, event):
        self.send(json.dumps({
            "status": "success",
            "event": "video_call",
            "data": event['data'],
        }))

    def video_call_end(self, event):
        self.send(json.dumps({
            "status": "success",
            "event": "video_call_end",
            "data": event['data'],
        }))

    def user_notfound(self, event):
        self.send(json.dumps({
            "status": "error",
            "data": event['data']
        }))


class VideoChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("VIDEOCHAT CONNECTED", self.scope["path"])
        print("PATH:", self.scope["path"])
        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'video_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        receive_dict = json.loads(text_data)
        message = receive_dict['message']
        action = receive_dict['action']

        if (action == 'new-offer') or (action == 'new-answer'):
            receiver_channel_name = receive_dict['message']['receiver_channel_name']

            receive_dict['message']['receiver_channel_name'] = self.channel_name

            await self.channel_layer.send(
                receiver_channel_name,
                {
                    'type': 'send.sdp',
                    'receive_dict': receive_dict
                }
            )

            return

        receive_dict['message']['receiver_channel_name'] = self.channel_name

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send.sdp',
                'receive_dict': receive_dict
            }
        )

    async def send_sdp(self, event):
        receive_dict = event['receive_dict']
        chat_id = self.room_name
        current_user = self.scope["user"]
        # data = await createVideoChat(chat_id, current_user)
        # print(data)
        await self.send(text_data=json.dumps(receive_dict))
