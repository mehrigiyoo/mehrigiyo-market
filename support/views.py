from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializer import OperatorProfileUpdateSerializer

class OperatorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = OperatorProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.operator_profile
