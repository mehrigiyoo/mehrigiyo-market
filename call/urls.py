from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallViewSet

router = DefaultRouter()
router.register(r'calls', CallViewSet, basename='call')

urlpatterns = [
    path('', include(router.urls)),
]

# Generated URLs:
# POST   /api/calls/initiate/
# POST   /api/calls/{id}/answer/
# POST   /api/calls/{id}/reject/
# POST   /api/calls/{id}/end/
# GET    /api/calls/
# GET    /api/calls/{id}/
# GET    /api/calls/active/
# GET    /api/calls/history/