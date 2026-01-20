from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from account.models import SmsCode
from client.serializer import ClientRegisterSerializer, ClientProfileSerializer, ClientAvatarSerializer
from config.responses import ResponseSuccess
from config.validators import normalize_phone


# views.py
class ClientProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.client_profile


class ClientRegisterView(APIView):
    def post(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # phone ni normalize qilamiz
        phone = normalize_phone(serializer.validated_data['phone'])

        # Confirmed SMS qidiramiz
        sms_qs = SmsCode.objects.filter(
            phone=phone,
            confirmed=True,
            expire_at__gte=timezone.now()
        )
        if not sms_qs.exists():
            return Response(
                {"detail": "SMS tasdiqlanmagan yoki muddati o'tgan"},
                status=400
            )

        # SMS code ni bekor qilamiz
        sms_qs.update(confirmed=False)

        # User yaratamiz
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=201)


class ClientAvatarUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ClientAvatarSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.avatar = serializer.validated_data['avatar']
        user.save()

        return ResponseSuccess(
            data={"avatar": user.avatar.url if user.avatar else None},
            request=request.method
        )