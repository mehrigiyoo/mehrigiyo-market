from django.urls import path

from .views import ChatView, MyChatsView, MessageView, FileMessageView, TgEndpointView, AdminAndDoctorChatRoomsAPIView

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('messages/', MessageView.as_view(), name='chat'),
    path('rooms/', MyChatsView.as_view(), name='chat'),
    path('file/', FileMessageView.as_view()),

    path('tg/endpoint', TgEndpointView.as_view()),
    path('all-room/', AdminAndDoctorChatRoomsAPIView.as_view()),

]
