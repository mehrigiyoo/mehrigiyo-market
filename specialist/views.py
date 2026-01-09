import uuid
from django.db.models import Sum, Avg, Count
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework import generics

import datetime
import pytz

from account.models import UserModel
from chat.models import ChatRoom
from config.responses import ResponseSuccess, ResponseFail
from specialist.methods import notify_doctors
from .serializers import TypeDoctorSerializer, DoctorSerializer, RateSerializer, AdvertisingSerializer, \
    AdviceSerializer, AdvicecDocSerializer, GenderStatisticsSerializer
from .models import Doctor, TypeDoctor, AdviceTime, Advertising
from .filters import DoctorFilter

utc = pytz.UTC


class AdvertisingView(generics.ListAPIView):
    queryset = Advertising.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = AdvertisingSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(
        operation_id='advertising',
        operation_description="advertisingView",
        # request_body=AdvertisingSerializer(),
        responses={
            '200': AdvertisingSerializer()
        },
    )
    def get(self, request, *args, **kwargs):

        return self.list(request, *args, **kwargs)


class TypeDoctorView(generics.ListAPIView):
    queryset = TypeDoctor.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = TypeDoctorSerializer

    @swagger_auto_schema(
        operation_id='get_doctor_types',
        operation_description="get_doctor_types",
        # request_body=TypeDoctorSerializer(),
        responses={
            '200': TypeDoctorSerializer()
        },

    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class DoctorsView(generics.ListAPIView):
    queryset = Doctor.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = DoctorSerializer
    filterset_class = DoctorFilter

    @swagger_auto_schema(
        operation_id='get_doctors',
        operation_description="get_doctors",
        # request_body=DoctorSerializer(),
        responses={
            '200': DoctorSerializer()
        },
        manual_parameters=[
            openapi.Parameter('type_ides', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        key = request.GET.get('type_ides', False)
        queryset = self.queryset.annotate(
            total_rate=Avg('comments_doc__rate')
        ).order_by('-total_rate')
        filtered_qs = self.filterset_class(request.GET, queryset=queryset).qs
        for i in filtered_qs:
            i.review = i.review + 1
            i.save()
        self.queryset = filtered_qs
        if key:
            keys = key.split(',')
            self.queryset = self.queryset.filter(type_doctor_id__in=keys)
        return self.list(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super(DoctorsView, self).get_serializer_context()
        context.update({'user': self.request.user})
        return context


class DoctorRetrieveView(generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    @swagger_auto_schema(
        operation_id='doctor-detail',
        operation_description="retrieving the doctor",
        responses={
            '200': DoctorSerializer()
        },
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class GetDoctorsWithType(generics.ListAPIView):
    queryset = Doctor.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = DoctorSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        manual_parameters=[
        openapi.Parameter('type_ides', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
    ], operation_description='GET /articles/today/')
    @action(detail=False, methods=['get'])
    def get(self, request, *args, **kwargs):
        key = request.GET.get('type_ides', False)
        print('rabotaet')
        if key:
            print('rabotaet')
            keys = key.split(',')
            print(keys, '---------------')
            self.queryset = self.queryset.filter(type_doctor_id__in=keys)
            print('333333333333')
        return self.list(request, *args, **kwargs)


class GetSingleDoctor(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = DoctorSerializer

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('pk', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_NUMBER)
    ])
    def get(self, request):
        key = request.GET.get('pk', False)
        from django.db.models import Avg
        queryset = self.queryset.annotate(
            total_rate=Avg('comments_doc__rate')
        )

        if key:
            queryset = Doctor.objects.get(id=key)
            queryset.review = queryset.review + 1
            queryset.save()
        serializer = self.get_serializer(queryset, context={'user': request.user})

        return ResponseSuccess(data=serializer.data, request=request.method)


class RateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = RateSerializer(data=request.data,
                                    context={'request': request},
                                    required=False)

        if serializer.is_valid():
            serializer.save()
            return ResponseSuccess(data=serializer.data)
        else:
            return ResponseFail(data=serializer.errors)


class AdviceView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='get_advice_times',
        operation_description="get_advice_times",
        # request_body=DoctorSerializer(),
        responses={
            '200': AdviceSerializer()
        },
        manual_parameters=[
            openapi.Parameter('day', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('month', openapi.IN_QUERY,  type=openapi.TYPE_INTEGER),
            openapi.Parameter('year', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),

            openapi.Parameter('my', openapi.IN_QUERY, description="all clients time", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
        ]
    )
    def get(self, request):
        day = request.GET.get('day', False)
        month = request.GET.get('month', False)
        year = request.GET.get('year', False)
        my = request.GET.get('my', False)
        pk = request.GET.get('id', False)
        if day:
            if my:
                advice = AdviceTime.objects.filter(doctor_id=pk,
                                                client=request.user,
                                                start_time__day=day,
                                                start_time__month=month,
                                                start_time__year=year)
            else:
                advice = AdviceTime.objects.filter(doctor_id=pk,
                                                start_time__day=day,
                                                start_time__month=month,
                                                start_time__year=year)
        else:
            if my:
                if pk:
                    advice = AdviceTime.objects.filter(doctor_id=pk,
                                                client=request.user, start_time__gte=datetime.datetime.now())
                else:
                    advice = AdviceTime.objects.filter(client=request.user, start_time__gte=datetime.datetime.now())
            else:
                advice = AdviceTime.objects.filter(doctor_id=pk, start_time__gte=datetime.datetime.now())

        ser = AdviceSerializer(advice, many=True)
        return ResponseSuccess(data=ser.data)


    @swagger_auto_schema(
        operation_id='post_advice_times',
        operation_description="post_advice_times",
        request_body=AdvicecDocSerializer(),
        responses={
            '200': AdviceSerializer()
        },
        # manual_parameters=[
        #     openapi.Parameter('day', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        #     openapi.Parameter('month', openapi.IN_QUERY,  type=openapi.TYPE_INTEGER),
        #     openapi.Parameter('year', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),

        #     openapi.Parameter('my', openapi.IN_QUERY, description="all clients time", type=openapi.TYPE_BOOLEAN)
        # ]
    )
    def post(self, request):
        date_time_start = request.data['start_time']
        date_time_end = request.data['end_time']
        pk = request.data['id']

        date_time_start_obj = date_time_start
        #  datetime.datetime.strptime(date_time_start, '%d/%m/%y %H:%M:%S')
        date_time_end_obj = date_time_end
        # datetime.datetime.strptime(date_time_end, '%d/%m/%y %H:%M:%S')

        advice = None
        try:
            advice = AdviceTime.objects.get(start_time=date_time_start_obj, end_time=date_time_end_obj)
        except:
            pass

        if advice is not None:
            return ResponseFail(data="Doktor bu vaqt oralig'ida band!")

        advice = AdviceTime()
        advice.client = request.user
        advice.doctor = Doctor.objects.get(id=pk)
        advice.start_time = date_time_start_obj
        advice.end_time = date_time_end_obj
        advice.save()

        # Send notifier message to Telegram
        TIME_FORMAT = "%d/%m/%Y %H:%M"

        start_time = datetime.datetime.fromisoformat(date_time_start_obj.replace('Z', '+05:00')).__add__(datetime.timedelta(hours=5)).strftime(TIME_FORMAT)
        end_time = datetime.datetime.fromisoformat(date_time_end_obj.replace('Z', '+05:00')).__add__(datetime.timedelta(hours=5)).strftime(TIME_FORMAT)

        notify_doctors(advice.id, start_time=start_time, end_time=end_time)

        # Create chat room after creating advice

        try:
            doctor = Doctor.objects.get(id=pk)
        except:
            return ResponseFail(data='Doctor not Found')

        try:
            doctor_user = UserModel.objects.get(specialist_doctor=doctor, is_staff=True)
        except:
            return ResponseFail(data='Doctor not Found')

        try:
            chatroom = ChatRoom.objects.get(client=request.user, doktor=doctor_user)
        except:
            chatroom = None

        if chatroom is None:
            chatroom = ChatRoom()
            chatroom.client = request.user
            chatroom.doktor = doctor_user
            chatroom.token = uuid.uuid4()
            chatroom.save()

        return ResponseSuccess()



#Doctor gender statistic

class GenderStatisticsView(APIView):
    def get(self, request, *args, **kwargs):
        total_doctors = Doctor.objects.count()

        if total_doctors == 0:
            data = {
                'total_doctors': total_doctors,
                'male_percentage': 0,
                'female_percentage': 0,
                'male_count': 0,
                'female_count': 0
            }
        else:
            gender_counts = Doctor.objects.values('gender').annotate(count=Count('gender'))
            gender_counts_dict = {item['gender']: item['count'] for item in gender_counts}

            male_count = gender_counts_dict.get('male', 0)
            female_count = gender_counts_dict.get('female', 0)

            male_percentage = (male_count / total_doctors) * 100
            female_percentage = (female_count / total_doctors) * 100

            data = {
                'total_doctors': total_doctors,
                'male_percentage': male_percentage,
                'female_percentage': female_percentage,
                'male_count': male_count,
                'female_count': female_count
            }

        serializer = GenderStatisticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

