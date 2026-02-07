from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, MessageViewSet, DoctorChatRoomViewSet

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'doctor/chat-rooms', DoctorChatRoomViewSet, basename='doctor-chat-room')


urlpatterns = [
    path('', include(router.urls)),
]