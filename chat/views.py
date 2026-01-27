from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import ChatRoom, Message, MessageAttachment


class UploadMessageAttachment(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # for file upload

    def post(self, request, room_id):
        """
        Attach file (image/video) to a message.
        """
        user = request.user

        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Room not found"}, status=404)

        if user not in room.participants.all() and user.role != 'operator':
            return Response({"error": "Not allowed"}, status=403)

        file = request.FILES.get('file')
        file_type = request.data.get('file_type', 'file')  # image / video / file
        size = file.size if file else 0

        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        # Create a new message if text provided
        text = request.data.get('text', '')

        message = Message.objects.create(room=room, sender=user, text=text)
        attachment = MessageAttachment.objects.create(
            message=message,
            file=file,
            file_type=file_type,
            size=size
        )

        return Response({
            "message_id": message.id,
            "text": message.text,
            "attachment": {
                "file": attachment.file.url,
                "file_type": attachment.file_type,
                "size": attachment.size
            }
        })
