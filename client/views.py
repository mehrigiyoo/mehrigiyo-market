from django.db import transaction, models
from django.db.models import OuterRef, Exists, Count, BooleanField, Value, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from account.models import SmsCode
from client.models import ClientAddress, MedicineLike
from client.serializer import ClientRegisterSerializer, ClientProfileSerializer, ClientAvatarSerializer, \
    ClientAddressSerializer
from config.responses import ResponseSuccess
from config.validators import normalize_phone
from shop.models import Medicine
from shop.serializers import MedicineSerializer


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



class ClientAddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = ClientAddress.objects.filter(user=request.user, is_active=True).order_by('-is_default', '-created_at')
        serializer = ClientAddressSerializer(addresses, many=True)
        return ResponseSuccess(data=serializer.data, request=request.method)

    @transaction.atomic
    def post(self, request):
        serializer = ClientAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Agar is_default True bo'lsa, eski defaultni o'chiramiz
        if serializer.validated_data.get('is_default'):
            ClientAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
        serializer.save(user=request.user)
        return ResponseSuccess(data=serializer.data, request=request.method)


class ClientAddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(ClientAddress, pk=pk, user=user, is_active=True)

    def get(self, request, pk):
        address = self.get_object(pk, request.user)
        serializer = ClientAddressSerializer(address)
        return ResponseSuccess(data=serializer.data, request=request.method)

    @transaction.atomic
    def put(self, request, pk):
        address = self.get_object(pk, request.user)
        serializer = ClientAddressSerializer(address, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('is_default'):
            ClientAddress.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)
        serializer.save()
        return ResponseSuccess(data=serializer.data, request=request.method)

    @transaction.atomic
    def delete(self, request, pk):
        address = self.get_object(pk, request.user)
        address.is_active = False  # Soft delete
        address.save(update_fields=['is_active'])
        return ResponseSuccess(data="Address removed", request=request.method)


class ClientAddressBulkDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return ResponseSuccess(data="No IDs provided", request=request.method)
        qs = ClientAddress.objects.filter(user=request.user, id__in=ids, is_active=True)
        affected = qs.update(is_active=False)
        return ResponseSuccess(data=f"{affected} addresses removed", request=request.method)




def get_queryset(self):
    user = self.request.user

    qs = Medicine.objects.filter(is_active=True).annotate(
        likes_count=Count('likes', distinct=True)
    )

    if user.is_authenticated:
        qs = qs.annotate(
            is_favorite=Exists(
                MedicineLike.objects.filter(
                    user=user,
                    medicine=OuterRef('pk')
                )
            )
        )
    else:
        qs = qs.annotate(is_favorite=models.Value(False))

    return qs


class MedicineLikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        medicine = get_object_or_404(Medicine, pk=pk, is_active=True)

        like, created = MedicineLike.objects.get_or_create(
            user=request.user,
            medicine=medicine
        )

        if not created:
            like.delete()
            return ResponseSuccess(
                data={"liked": False},
                request=request.method
            )

        return ResponseSuccess(
            data={"liked": True},
            request=request.method
        )


class FavoriteMedicineListAPIView(generics.ListAPIView):
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return (
            Medicine.objects
            .filter(likes__user=user, is_active=True)
            .annotate(
                total_rate=Avg('comments_med__rate'),
                likes_count=Count('likes', distinct=True),
                is_favorite=Value(True, output_field=BooleanField())
            )
            .select_related('type_medicine')
            .prefetch_related('pictures')
        )
