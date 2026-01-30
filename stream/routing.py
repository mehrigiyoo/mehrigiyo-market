from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/stream/<int:stream_id>/', consumers.LiveStreamConsumer.as_asgi()),
]