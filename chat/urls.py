from django.urls import path
from .views import UploadMessageAttachment

urlpatterns = [
    path('upload/<int:room_id>/', UploadMessageAttachment.as_view(), name='upload_message_attachment'),
]
