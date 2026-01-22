import datetime
import pytz
from django.db import transaction, models
from django.db.utils import IntegrityError
from django.db.models import Count
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework import generics

from account.models import SmsCode
from config.responses import ResponseSuccess
from .permissions import IsDoctor
from .serializers import TypeDoctorSerializer, RateSerializer, AdvertisingSerializer, \
    GenderStatisticsSerializer, AdviceTimeSerializer, AvailableSlotSerializer, \
    DoctorUnavailableSerializer, WorkScheduleSerializer, DoctorProfileSerializer, \
    DoctorRegisterSerializer, DoctorListSerializer, DoctorDetailSerializer
from .models import Doctor, TypeDoctor, Advertising, AdviceTime, DoctorUnavailable, WorkSchedule, DoctorView
from .services import create_advice_service
from django.contrib.auth import get_user_model
UserModel = get_user_model()

utc = pytz.UTC


class AdvertisingView(generics.ListAPIView):
    serializer_class = AdvertisingSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_queryset(self):
        return Advertising.objects.select_related('doctor')


class TypeDoctorView(generics.ListAPIView):
    queryset = TypeDoctor.objects.all()
    serializer_class = TypeDoctorSerializer
    permission_classes = [AllowAny]



class DoctorProfileView(RetrieveUpdateAPIView):
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_object(self):
        doctor, created = Doctor.objects.get_or_create(
            user=self.request.user,
            defaults={
                "full_name": "",
                "experience": "",
                "gender": "male",
                "type_doctor_id": 1,
            }
        )
        return doctor



class DoctorRegisterView(APIView):
    def post(self, request):
        serializer = DoctorRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']

        # SMS tasdiqlanganmi?
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

        # SMS code qayta ishlatilmasin
        sms_qs.update(confirmed=False)

        serializer.save()

        return Response(
            {
                "detail": (
                    "Ro‘yxatdan o‘tdingiz. "
                    "Profilingiz admin tomonidan tasdiqlangach login qilishingiz mumkin."
                )
            },
            status=201
        )


# Doctorlar listini olish va type bo'yicha filter qilish
class DoctorListAPI(generics.ListAPIView):
    serializer_class = DoctorListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Doctor.objects.filter(is_verified=True).order_by('-top', '-review')
        type_id = self.request.GET.get('type', None)
        if type_id:
            queryset = queryset.filter(type_doctor_id=type_id)
        return queryset


# Doctor detalini olish
class DoctorDetailAPI(generics.RetrieveAPIView):
    queryset = Doctor.objects.filter(is_verified=True)
    serializer_class = DoctorDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        doctor = self.get_object()
        user = request.user

        # Atomic block (race condition oldini oladi)
        try:
            with transaction.atomic():
                DoctorView.objects.create(
                    doctor=doctor,
                    user=user
                )
                # faqat 1-marta kirilganda oshadi
                Doctor.objects.filter(id=doctor.id).update(
                    view_count=models.F('view_count') + 1
                )
        except IntegrityError:
            # bu user oldin ko‘rgan — hech narsa qilmaymiz
            pass

        serializer = self.get_serializer(doctor)
        return Response(serializer.data)


class GetSingleDoctor(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = DoctorProfileSerializer

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


class RateView(generics.CreateAPIView):
    serializer_class = RateSerializer
    permission_classes = [IsAuthenticated]



class WorkScheduleViewSet(viewsets.ModelViewSet):
    """
    Admin yoki Doctor o'z ish jadvalini boshqaradi
    """
    queryset = WorkSchedule.objects.all()
    serializer_class = WorkScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'doctor_profile'):
            return WorkSchedule.objects.filter(doctor=user.doctor_profile)
        return WorkSchedule.objects.all()


class DoctorUnavailableViewSet(viewsets.ModelViewSet):
    """
    Admin yoki Doctor ishlay olmaydigan kunlarini boshqaradi
    """
    queryset = DoctorUnavailable.objects.all()
    serializer_class = DoctorUnavailableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'doctor_profile'):
            return DoctorUnavailable.objects.filter(doctor=user.doctor_profile)
        return DoctorUnavailable.objects.all()


class AvailableSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Mobile clientga berish uchun bo‘sh vaqtlar
        Params: doctor_id, date (YYYY-MM-DD)
        """
        doctor_id = request.GET.get('doctor_id')
        date_str = request.GET.get('date')
        if not doctor_id or not date_str:
            return Response({"error": "doctor_id va date kerak"}, status=status.HTTP_400_BAD_REQUEST)

        doctor = Doctor.objects.get(id=doctor_id)
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Doctor ishlay olmaydigan kunlar
        if DoctorUnavailable.objects.filter(doctor=doctor, date=date).exists():
            return Response([])  # Hech qanday slot yo'q

        # Doctor ish jadvali
        weekday = date.weekday()
        schedules = WorkSchedule.objects.filter(doctor=doctor, weekday=weekday)
        available_slots = []

        for sched in schedules:
            start_dt = datetime.combine(date, sched.start_time)
            end_dt = datetime.combine(date, sched.end_time)

            # Har bir slotni 30 daqiqalik intervallarda bo‘lamiz
            slot_start = start_dt
            while slot_start + datetime.timedelta(minutes=30) <= end_dt:
                slot_end = slot_start + datetime.timedelta(minutes=30)
                # Band bo‘lmagan slot
                if not AdviceTime.objects.filter(
                    doctor=doctor,
                    start_time__lt=slot_end,
                    end_time__gt=slot_start
                ).exists():
                    available_slots.append({
                        "start_time": slot_start,
                        "end_time": slot_end
                    })
                slot_start += datetime.timedelta(minutes=30)

        serializer = AvailableSlotSerializer(available_slots, many=True)
        return Response(serializer.data)


class BookAdviceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Client slotni bron qiladi
        Params: doctor_id, start_time, end_time
        """
        client = request.user
        doctor_id = request.data.get("doctor_id")
        start_time = request.data.get("start_time")
        end_time = request.data.get("end_time")

        try:
            advice = create_advice_service(
                client=client,
                doctor_id=doctor_id,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AdviceTimeSerializer(advice)
        return Response(serializer.data)

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

