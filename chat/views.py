from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import UserModel
from config.responses import ResponseFail, ResponseSuccess
from paymeuz.keywords import TELEGRAM_CHAT_GROUP_ID
from .models import ChatRoom, Message, FileMessage
from .serializers import ChatSerializer, RoomsSerializer, MessageSerializer, FileMessageSerializer, \
    ChatRoomAndDoctorSerializer


class TgEndpointView(APIView):
    def post(self, request: Request):
        message = request.data['message']

        if message is None:
            print("not a telegram payload")
            return ResponseFail(data="error")

        if not 'text' in message:
            print("not a message")
            return ResponseFail(data="allowed only messages")

        if str(message['chat']['id']) != str(TELEGRAM_CHAT_GROUP_ID):
            print("another telegram chat")
            return ResponseFail(data="another telegram chat")

        # async_to_sync(self.sendToWS(message=message['text']))
        # self.sendToWS(message=message['text'])

        # print(json.dumps(request.data, indent=4))
        self.saveMessage(_message=message['text'], _thread_id=message['message_thread_id'])
        return ResponseSuccess(data="ok")

    def saveMessage(self, _message: str, _thread_id: int):
        try:
            chatroom = ChatRoom.objects.get(thread_id=_thread_id)
        except:
            return False

        try:
            message = Message()
            message.text = _message
            message.owner = chatroom.doktor
            message.save()
        except:
            return False

        chatroom.messages.add(message)
        chatroom.save()

        return True

    # async def sendToWS(self, message: str):
    #     print(message)
    #     async with websockets.connect('ws://127.0.0.1:8000/chat/2/') as websocket:
    #         await websocket.send('asd')
    #         await websocket.close()


class ChatView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        responses={
            '200': ChatSerializer()
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="pk",
                              type=openapi.TYPE_NUMBER),
            openapi.Parameter('admin', openapi.IN_QUERY, description="chat with admin",
                              type=openapi.TYPE_BOOLEAN)
        ], operation_description='GET News')
    @action(detail=False, methods=['get'])
    def get(self, request):
        key = request.GET.get('pk', False)
        admin = False if (request.GET.get('admin', False) == "false") or (
                request.GET.get('admin', False) == False) else True

        if admin:
            user = UserModel.objects.filter(is_superuser=True).first()
            try:
                room = ChatRoom.objects.get(client=request.user, admin=user)
            except:
                room = None
            if room is None:
                from uuid import uuid4
                rand_token = uuid4()
                room = ChatRoom()
                room.client = request.user
                room.admin = user
                room.token = rand_token
                room.save()

            serializer = ChatSerializer(room)
            return ResponseSuccess(data=serializer.data, request=request.method)

        if key:
            try:
                user = UserModel.objects.get(id=key)
            except:
                return ResponseFail(data='User not Found')

            rooms_query = Q()

            rooms_query1 = Q(client=request.user)
            rooms_query1.add(Q(doktor=user), Q.AND)

            rooms_query2 = Q(client=user)
            rooms_query2.add(Q(doktor=request.user), Q.AND)

            rooms_query.add(Q(rooms_query1), Q.OR)
            rooms_query.add(Q(rooms_query2), Q.OR)

            # try:
            #     doctor = Doctor.objects.get(id=key)
            # except:
            #     return ResponseFail(data='Doctor not Found')

            # try:
            #     user = UserModel.objects.get(specialist_doctor=doctor, is_staff=True)
            # except:
            #     return ResponseFail(data='Doctor not Found')

            try:
                room = ChatRoom.objects.get(rooms_query)
            except:
                room = None

            # if room is None:
            #     room = ChatRoom()
            #     room.client = request.user
            #     room.doktor = user
            #     room.token = uuid.uuid4()
            #     room.save()

            serializer = ChatSerializer(room)
            return ResponseSuccess(data=serializer.data, request=request.method)

        return ResponseFail(data="Tere is no key, no admin!")


class FileMessageView(APIView):
    # permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='file_mess',
        operation_description="File Message",
        responses={
            '200': FileMessageSerializer()
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="File ID",
                              type=openapi.TYPE_NUMBER),
        ],
    )
    def get(self, request):
        key = request.GET.get('pk', False)
        if key:
            file = FileMessage.objects.get(id=key)
            serializer = FileMessageSerializer(file)
            return ResponseSuccess(serializer.data)
        return ResponseFail(data="File not found")

    @swagger_auto_schema(
        operation_id='file_mess_create',
        operation_description="File Message Create",
        request_body=FileMessageSerializer,
        responses={
            '200': FileMessageSerializer()
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="File ID",
                              type=openapi.TYPE_NUMBER),
        ],
    )
    def post(self, request):
        serializer = FileMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseSuccess(data=serializer.data)
        else:
            return ResponseFail(data=serializer.errors)


class MyChatsView(generics.ListAPIView):
    queryset = ChatRoom.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RoomsSerializer

    @swagger_auto_schema(
        operation_id='chat_view',
        operation_description="chat_view",
        # request_body=RoomsSerializer(),
        responses={
            '200': RoomsSerializer()
        },
    )
    def get(self, request, *args, **kwargs):
        rooms_query = Q(client=request.user)
        rooms_query.add(Q(doktor=request.user), Q.OR)

        rooms = ChatRoom.objects.filter(rooms_query)
        # ad = AdviceTime.objects.filter(client=request.user, start_time__gte=datetime.datetime.now()).first()
        # print(ad)
        self.queryset = rooms
        # serializer = RoomsSerializer(rooms, many=True)
        return self.list(request, *args, **kwargs)


class MessageView(generics.ListAPIView):
    queryset = Message.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer

    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        responses={
            '200': MessageSerializer()
        },
        manual_parameters=[
            openapi.Parameter('chat_id', openapi.IN_QUERY, description="chat_id",
                              type=openapi.TYPE_NUMBER)
        ], operation_description='get all messages with pagination')
    def get(self, request, *args, **kwargs):
        key = request.GET.get('chat_id', False)
        if key:
            chr = ChatRoom.objects.get(id=key)
            self.queryset = chr.messages.all().order_by('-id')
        return self.list(request, *args, **kwargs)


class AdminAndDoctorChatRoomsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({'detail': 'You do not have permission to perform this action.'}, status=403)

        # Admin yoki doktor sifatida ochilgan barcha chat xonalarini olish
        chat_rooms = ChatRoom.objects.filter(
            Q(admin__isnull=False) | Q(doktor__isnull=False)
        ).distinct()

        serializer = ChatRoomAndDoctorSerializer(chat_rooms, many=True)

        return Response(serializer.data)