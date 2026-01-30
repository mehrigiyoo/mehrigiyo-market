
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import LiveStreamViewSet, StreamChatViewSet, StreamReactionViewSet

# Main router
router = DefaultRouter()
router.register(r'streams', LiveStreamViewSet, basename='livestream')

# Nested routers for chat and reactions
streams_router = routers.NestedDefaultRouter(router, r'streams', lookup='stream')
streams_router.register(r'chat', StreamChatViewSet, basename='stream-chat')
streams_router.register(r'reactions', StreamReactionViewSet, basename='stream-reactions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(streams_router.urls)),
]
