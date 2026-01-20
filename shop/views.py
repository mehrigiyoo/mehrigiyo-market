from django.conf import settings
from django.db.models import Avg, Count, Q
from drf_yasg import openapi
from google.cloud.firestore_v1.order import Order
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from paymeuz.methods import send_order
from paymeuz.models import Card
from .filters import ProductFilter
from account.models import DeliveryAddress
from config.responses import ResponseSuccess, ResponseFail
from .serializers import (TypeMedicineSerializer, MedicineSerializer, CartSerializer, OrderCreateSerializer,
                          OrderShowSerializer, ListSerializer, CartPostSerializer,
                          OrderPutSerializer, CartPutSerializer, PutSerializer, OrderStatusSerializer,
                          MedicineTypeSerializer)
from .models import TypeMedicine, Medicine, CartModel, OrderModel
from rest_framework import viewsets, generics
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
    queryset = Medicine.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = MedicineSerializer
    filterset_class = ProductFilter

    @swagger_auto_schema(
        operation_id='get_doctors',
        operation_description="get_doctors",
        # request_body=DoctorSerializer(),
        responses={
            '200': MedicineSerializer()
        },
        manual_parameters=[
            openapi.Parameter('type_ides', openapi.IN_QUERY, description="test manual param",
                              type=openapi.TYPE_STRING)
        ],
    )
    def get(self, request, *args, **kwargs):
        key = request.GET.get('type_ides', False)

        queryset = self.queryset.annotate(
            total_rate=Avg('comments_med__rate')
        ).order_by('-id')
        filtered_qs = self.filterset_class(request.GET, queryset=queryset).qs
        for i in filtered_qs:
            i.review = i.review + 1
            i.save()
        self.queryset = filtered_qs
        if key:
            keys = key.split(',')
            self.queryset = self.queryset.filter(type_medicine_id__in=keys)

        return self.list(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super(MedicinesView, self).get_serializer_context()
        context.update({'user': self.request.user})
        return context


class MedicineRetrieveView(generics.RetrieveAPIView):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer

    @swagger_auto_schema(
        operation_id='doctor-detail',
        operation_description="retrieving the doctor",
        responses={
            '200': MedicineSerializer()
        },
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


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
    permission_classes = (IsAuthenticated,)
    serializer_class = CartSerializer

    @swagger_auto_schema(
        operation_id='get_Cart',
        operation_description="get_Cart",
        responses={
            '200': CartSerializer()
        },

    )
    def get(self, request):
        carts = CartModel.objects.filter(user=request.user, status=1)
        serializer = CartSerializer(carts, many=True, context={'request': request, 'user': request.user})
        return ResponseSuccess(data=serializer.data, request=request.method)

    @swagger_auto_schema(
        operation_id='create_Cart',
        operation_description="send product id and amount ",
        request_body=CartPostSerializer(),
        responses={
            '200': CartSerializer()
        },

    )
    def post(self, request):
        med = Medicine.objects.get(id=request.data['product'])
        try:
            serializer = CartModel.objects.get(user=request.user, status=1, product=med)
            return ResponseSuccess(data='This product alredy in the cart', request=request.method)
        except:
            serializer = CartSerializer(data=request.data, context={'request': request,
                                                                    'user': request.user})

        if serializer.is_valid():
            cart = CartModel.objects.create(user=request.user, product=med, amount=request.data['amount'])

            # serializer.save()
            serializer = CartSerializer(cart)
            return ResponseSuccess(data=serializer.data, request=request.method)
        else:
            return ResponseFail(data=serializer.errors, request=request.method)

    @swagger_auto_schema(
        operation_id='update_Cart',
        operation_description="UpdateCart",
        request_body=CartPutSerializer(),
        responses={
            '200': CartSerializer()
        },

    )
    def put(self, request):
        cart = CartModel.objects.get(id=request.data['id'], user=request.user)
        del request.data['id']
        serializer = CartSerializer(cart, data=request.data, context={'request': request,
                                                                      'user': request.user})
        if serializer.is_valid():
            serializer.save()
            return ResponseSuccess(data=serializer.data, request=request.method)
        else:
            return ResponseFail(data=serializer.errors, request=request.method)

    @swagger_auto_schema(
        operation_id='delete_Cart',
        operation_description="DeleteCart",
        request_body=PutSerializer(),
        responses={
            '200': CartSerializer()
        },

    )
    def delete(self, request):
        try:
            CartModel.objects.get(id=request.data['id'], user=request.user).delete()
            return ResponseSuccess(request=request.method)
        except:
            return ResponseFail(request=request.method)


class OrderView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartSerializer

    @swagger_auto_schema(
        operation_id='get_order_model',
        operation_description="get_order_model",
        # request_body=OrderShowSerializer(),
        responses={
            '200': OrderShowSerializer()
        },

    )
    def get(self, request):
        orders = OrderModel.objects.filter(user=request.user)
        serializer = OrderShowSerializer(orders, many=True)
        return ResponseSuccess(data=serializer.data, request=request.method)

    @swagger_auto_schema(
        operation_id='create_cart_model',
        operation_description="To create cart model",
        request_body=ListSerializer(),
        responses={
            '200': OrderShowSerializer()
        },

    )
    def post(self, request):
        ides = request.data['list'].split(',')
        carts = CartModel.objects.filter(user=request.user, status=1, id__in=ides)
        order = OrderModel()
        order.user = request.user
        order.save()
        summa = 0
        for i in carts:
            order.cart_products.add(i)
            summa += i.get_total_price
            # i.status = 2
            # i.save()
        order.price = summa
        order.save()
        serializer = OrderShowSerializer(order)
        return ResponseSuccess(data=serializer.data, request=request.method)

    @swagger_auto_schema(
        operation_id='create_order_model',
        operation_description="To add shipping address to order",
        request_body=OrderPutSerializer(),
        responses={
            '200': OrderShowSerializer()
        },

    )
    def put(self, request):
        credit_card = request.data['credit_card']
        cart = CartModel.objects.filter(user=request.user, status=1)
        card = None

        try:
            order = OrderModel.objects.get(id=request.data['id'])
        except:
            return ResponseFail(data='Order not found')

        try:
            id = request.data['shipping_address']
            da = DeliveryAddress.objects.get(id=id)
            add_key = 1
        except:
            add_key = 0

        if add_key == 1:
            order.shipping_address = da

        if credit_card is not None:
            try:
                card = Card.objects.get(id=request.data['credit_card'])
                # print(card, '<---------------------------------')
                order.credit_card = card
                order.payment_type = 2
            except:
                return ResponseFail(data='Credit Card Not found')
        else:
            order.payment_type = 1
            order.payment_status = 3
            order.save()

            send_order(order.id)

            for product in cart:
                product.status = 2
                product.save()

        try:
            del request.data['id']
            serializer = OrderCreateSerializer(order, data=request.data)
            if serializer.is_valid():
                if add_key == 1:
                    if order.shipping_address is None:
                        if da.region.delivery_price == 0:
                            order.price = order.price + settings.DEFAULT_DELIVERY_COST
                        else:
                            order.price = order.price + da.region.delivery_price
                    else:
                        old_price = order.shipping_address.region.delivery_price

                        if old_price == 0:
                            order.price = order.price - settings.DEFAULT_DELIVERY_COST
                        else:
                            order.price = order.price - old_price

                        if da.region.delivery_price == 0:
                            order.price = order.price + settings.DEFAULT_DELIVERY_COST
                        else:
                            order.price = order.price + da.region.delivery_price

                order.save()
                serializer.save()
                serializer = OrderShowSerializer(order)
                return ResponseSuccess(data=serializer.data, request=request.method)
            else:
                return ResponseFail(data=serializer.errors, request=request.method)
        except Exception as e:
            print(f'\n\nexception : {e}\n\n')


class SearchView(APIView):
    @swagger_auto_schema(
        operation_id='search',
        operation_description="Search",
        # request_body=RoomsSerializer(),
        manual_parameters=[
            openapi.Parameter('key', openapi.IN_QUERY, description="write key",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('medicines', openapi.IN_QUERY, description="medicines",
                              type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('doctors', openapi.IN_QUERY, description="doctors",
                              type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('news', openapi.IN_QUERY, description="news",
                              type=openapi.TYPE_BOOLEAN)
        ]
    )
    def get(self, request):
        key = request.GET.get('key', False)
        medicines = request.GET.get('medicines', False)
        doctors = request.GET.get('doctors', False)
        news = request.GET.get('news', False)

        data = {}
        if key:
            if medicines:
                med = []
                med.extend(Medicine.objects.filter(name__contains=key))
                med.extend(Medicine.objects.filter(type_medicine__name__contains=key))
                med.extend(Medicine.objects.filter(title__contains=key))
                med_ser = MedicineSerializer(med, many=True)
                data['medicines'] = med_ser.data
            if doctors:
                doc = []
                doc.extend(Doctor.objects.filter(full_name__contains=key))
                doc.extend(Doctor.objects.filter(type_doctor__name__contains=key))
                doc_ser = DoctorProfileSerializer(doc, many=True)
                data['doctors'] = doc_ser.data
            if news:
                new = []
                new.extend(NewsModel.objects.filter(name__contains=key))
                new.extend(NewsModel.objects.filter(description__contains=key))
                new_ser = NewsModelSerializer(new, many=True)
                data['news'] = new_ser.data

        return ResponseSuccess(data=data)


# Order statictic
class OrderStatusAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        client_count = AdviceTime.objects.values('client').distinct().count()
        total_orders = OrderModel.objects.count()
        doctor_count=Doctor.objects.count()
        product_total=Medicine.objects.count()
        delivered_count_all = OrderModel.objects.filter(delivery_status=3).count()


        statuses = OrderModel.objects.aggregate(
            delivered_count=Count('id', filter=Q(delivery_status=3)),
            in_progress_count=Count('id', filter=Q(delivery_status=2)),
            canceled_count=Count('id', filter=Q(delivery_status=4))
        )

        delivered_count = statuses['delivered_count']
        in_progress_count = statuses['in_progress_count']
        canceled_count = statuses['canceled_count']

        delivered_percentage = (delivered_count / total_orders) * 100 if total_orders > 0 else 0
        in_progress_percentage = (in_progress_count / total_orders) * 100 if total_orders > 0 else 0
        canceled_percentage = (canceled_count / total_orders) * 100 if total_orders > 0 else 0

        response_data = {
            'delivered_count': delivered_count,
            'delivered_percentage': delivered_percentage,
            'in_progress_count': in_progress_count,
            'in_progress_percentage': in_progress_percentage,
            'canceled_count': canceled_count,
            'canceled_percentage': canceled_percentage,
            'total_orders': total_orders,
            'doctor_count':doctor_count,
            'product_total':product_total,
            'client_count':client_count,
            'delivered_count_all':delivered_count_all,
        }

        serializer = OrderStatusSerializer(response_data)
        return Response(serializer.data)



class MedicineByTypeView(APIView):
    def get(self, request, type_medicine_id, *args, **kwargs):
        try:
            type_medicine = TypeMedicine.objects.get(id=type_medicine_id)
        except TypeMedicine.DoesNotExist:
            return Response({"error": "TypeMedicine not found"}, status=404)

        medicines = Medicine.objects.filter(type_medicine=type_medicine)
        serializer = MedicineTypeSerializer(medicines, many=True)
        return Response(serializer.data)

