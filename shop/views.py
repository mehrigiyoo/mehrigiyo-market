from django.db import transaction
from django.db.models import Avg, Count, Q, F
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from google.cloud.firestore_v1.order import Order
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .filters import ProductFilter
from config.responses import ResponseSuccess
from .serializers import (TypeMedicineSerializer, MedicineSerializer, CartSerializer,
                          OrderStatusSerializer,
                          MedicineTypeSerializer, CartCreateUpdateSerializer, MedicineDetailSerializer)
from .models import TypeMedicine, Medicine, CartModel
from rest_framework import viewsets, generics, filters
from drf_yasg.utils import swagger_auto_schema
from specialist.models import Doctor, AdviceTime
from specialist.serializers import DoctorProfileSerializer
from news.models import NewsModel
from news.serializers import NewsModelSerializer


class TypeMedicineView(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TypeMedicine.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = TypeMedicineSerializer

    @swagger_auto_schema(
        operation_id='get_medicines_types',
        operation_description="get_medicines_types",
        request_body=TypeMedicineSerializer(),
        responses={
            '200': TypeMedicineSerializer()
        },
        # method='get'
        # permission_classes=[IsAuthenticated, ],
        # tags=['photos'],
    )
    def get(self, request):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return ResponseSuccess(data=self.get_paginated_response(serializer.data), request=request.method)


class MedicinesView(generics.ListAPIView):
    serializer_class = MedicineSerializer
    filterset_class = ProductFilter

    def get_queryset(self):
        queryset = Medicine.objects.filter(is_active=True).select_related(
            'type_medicine'
        ).prefetch_related(
            'pictures'
        ).annotate(
            total_rate=Avg('comments_med__rate')
        ).order_by('-id')

        filtered_qs = self.filterset_class(self.request.GET, queryset=queryset).qs

        # type_ides filter
        key = self.request.GET.get('type_ides')
        if key:
            keys = key.split(',')
            filtered_qs = filtered_qs.filter(type_medicine_id__in=keys)

        # review ni bulk increment qilish
        filtered_qs.update(review=F('review') + 1)

        return filtered_qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'user': self.request.user})
        return context



class MedicineRetrieveView(generics.RetrieveAPIView):
    serializer_class = MedicineDetailSerializer

    def get_queryset(self):
        return (
            Medicine.objects.filter(is_active=True)
            .select_related('type_medicine')
            .prefetch_related('pictures', 'feedbacks')
            .annotate(total_rate=Avg('comments_med__rate'))
        )


class GetMedicinesWithType(generics.ListAPIView):
    queryset = Medicine.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = MedicineSerializer

    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        manual_parameters=[
            openapi.Parameter('type_ides', openapi.IN_QUERY, description="test manual param",
                              type=openapi.TYPE_STRING)
        ], operation_description='GET /articles/today/')
    @action(detail=False, methods=['get'])
    def get(self, request, *args, **kwargs):
        key = request.GET.get('type_ides', False)
        if key:
            keys = key.split(',')
            self.queryset = self.queryset.filter(type_medicine_id__in=keys)
        return self.list(request, *args, **kwargs)


class GetSingleMedicine(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer

    # permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('pk', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
    ])
    def get(self, request):
        key = request.GET.get('pk', False)
        queryset = self.queryset

        if key:
            queryset = self.queryset.filter(name__contains=key)
        serializer = self.get_serializer(queryset, context={'user': request.user})
        return ResponseSuccess(data=serializer.data, request=request.method)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    # GET CART
    def get(self, request):
        carts = (
            CartModel.objects
            .filter(user=request.user, status=CartModel.Status.ACTIVE)
            .select_related('product')
        )
        return ResponseSuccess(
            data=CartSerializer(carts, many=True, context={"request": request}).data,
            request=request.method
        )

    # ADD TO CART
    @transaction.atomic
    def post(self, request):
        serializer = CartCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(
            Medicine,
            id=serializer.validated_data['product_id'],
            is_active=True
        )
        amount = serializer.validated_data['amount']

        cart, created = CartModel.objects.select_for_update().get_or_create(
            user=request.user,
            product=product,
            status=CartModel.Status.ACTIVE,
            defaults={'amount': amount}
        )

        if not created:
            cart.amount += amount
            cart.save(update_fields=['amount'])

        return ResponseSuccess(
            data=CartSerializer(cart, context={"request": request}).data,
            request=request.method
        )

    # UPDATE AMOUNT
    @transaction.atomic
    def put(self, request):
        cart = get_object_or_404(
            CartModel,
            id=request.data.get('id'),
            user=request.user,
            status=CartModel.Status.ACTIVE
        )

        serializer = CartCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart.amount = serializer.validated_data['amount']
        cart.save(update_fields=['amount'])

        return ResponseSuccess(
            data=CartSerializer(cart, context={"request": request}).data,
            request=request.method
        )

    # DELETE
    @transaction.atomic
    def delete(self, request):
        """
        - Bitta item o‘chirish: id yuboriladi
        - Savatni to‘liq tozalash: id yuborilmasa
        """
        cart_id = request.data.get('id')
        user = request.user

        qs = CartModel.objects.filter(user=user)

        if cart_id:
            deleted, _ = qs.filter(id=cart_id).delete()

            if deleted == 0:
                return Response(
                    {"detail": "Cart item topilmadi"},
                    status=404
                )

            return ResponseSuccess(
                data={"removed_count": deleted},
                request=request.method
            )

        # CLEAR CART
        deleted, _ = qs.delete()

        if deleted == 0:
            return Response(
                {"detail": "Savat bo‘sh"},
                status=404
            )

        return ResponseSuccess(
            data={
                "removed_count": deleted,
                "message": "Savat to‘liq tozalandi"
            },
            request=request.method
        )



class MedicineSearchAPIView(generics.ListAPIView):
    queryset = Medicine.objects.filter(is_active=True)
    serializer_class = MedicineSerializer
    filter_backends = [filters.SearchFilter]

    search_fields = [
        'name',
        'title',
        'description',
        'type_medicine__name',
        'content_uz',
        'content_ru',
        'content_en',
    ]


class TypeMedicineSearchAPIView(generics.ListAPIView):
    queryset = TypeMedicine.objects.all()
    serializer_class = TypeMedicineSerializer
    filter_backends = [filters.SearchFilter]

    search_fields = ['name']


# Order statictic
# class OrderStatusAPIView(APIView):
#     permission_classes = (IsAuthenticated,)
#     def get(self, request, *args, **kwargs):
#         client_count = AdviceTime.objects.values('client').distinct().count()
#         total_orders = OrderModel.objects.count()
#         doctor_count=Doctor.objects.count()
#         product_total=Medicine.objects.count()
#         delivered_count_all = OrderModel.objects.filter(delivery_status=3).count()
#
#
#         statuses = OrderModel.objects.aggregate(
#             delivered_count=Count('id', filter=Q(delivery_status=3)),
#             in_progress_count=Count('id', filter=Q(delivery_status=2)),
#             canceled_count=Count('id', filter=Q(delivery_status=4))
#         )
#
#         delivered_count = statuses['delivered_count']
#         in_progress_count = statuses['in_progress_count']
#         canceled_count = statuses['canceled_count']
#
#         delivered_percentage = (delivered_count / total_orders) * 100 if total_orders > 0 else 0
#         in_progress_percentage = (in_progress_count / total_orders) * 100 if total_orders > 0 else 0
#         canceled_percentage = (canceled_count / total_orders) * 100 if total_orders > 0 else 0
#
#         response_data = {
#             'delivered_count': delivered_count,
#             'delivered_percentage': delivered_percentage,
#             'in_progress_count': in_progress_count,
#             'in_progress_percentage': in_progress_percentage,
#             'canceled_count': canceled_count,
#             'canceled_percentage': canceled_percentage,
#             'total_orders': total_orders,
#             'doctor_count':doctor_count,
#             'product_total':product_total,
#             'client_count':client_count,
#             'delivered_count_all':delivered_count_all,
#         }
#
#         serializer = OrderStatusSerializer(response_data)
#         return Response(serializer.data)



class MedicineByTypeView(APIView):
    def get(self, request, type_medicine_id, *args, **kwargs):
        try:
            type_medicine = TypeMedicine.objects.get(id=type_medicine_id)
        except TypeMedicine.DoesNotExist:
            return Response({"error": "TypeMedicine not found"}, status=404)

        medicines = Medicine.objects.filter(type_medicine=type_medicine)
        serializer = MedicineTypeSerializer(medicines, many=True, context={'request': request})
        return Response(serializer.data)

