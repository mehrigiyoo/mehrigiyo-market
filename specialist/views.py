import datetime
import pytz
from django.db import transaction, models
from django.db.utils import IntegrityError
from django.db.models import Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework import generics

from account.models import SmsCode
from consultation.models import ConsultationRequest
from .permissions import IsDoctor
from .serializers import TypeDoctorSerializer, AdvertisingSerializer, \
    GenderStatisticsSerializer, AdviceTimeSerializer, AvailableSlotSerializer, \
    DoctorUnavailableSerializer, WorkScheduleSerializer, DoctorProfileSerializer, \
    DoctorRegisterSerializer, DoctorListSerializer, DoctorDetailSerializer, DoctorRatingSerializer, \
    ConsultationDetailSerializer
from .models import Doctor, TypeDoctor, Advertising, AdviceTime, DoctorUnavailable, WorkSchedule, DoctorView, RateDoctor
from .services import create_advice_service
from django.contrib.auth import get_user_model
UserModel = get_user_model()

utc = pytz.UTC


class AdvertisingView(generics.ListAPIView):
    serializer_class = AdvertisingSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_queryset(self):
        return Advertising.objects.select_related('doctor')


class TypeDoctorListAPI(generics.ListAPIView):
    serializer_class = TypeDoctorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Faqat tasdiqlangan doctorlar hisoblanadi
        return TypeDoctor.objects.annotate(
            doctors_count=Count('doctor', filter=models.Q(doctor__is_verified=True))
        )



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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Doctor.objects.filter(is_verified=True).annotate(
            calculated_average_rating=Avg('ratings__rating'),
            calculated_rating_count=Count('ratings')
        ).order_by('-calculated_average_rating', '-top')

        type_id = self.request.GET.get('type')
        if type_id:
            queryset = queryset.filter(type_doctor_id=type_id)

        return queryset


# Doctor detalini olish
class DoctorDetailAPI(generics.RetrieveAPIView):
    serializer_class = DoctorDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Doctor.objects.filter(is_verified=True).annotate(
            calculated_average_rating=Avg('ratings__rating'),
            calculated_rating_count=Count('ratings')
        )

    def retrieve(self, request, *args, **kwargs):
        doctor = self.get_object()
        user = request.user

        try:
            with transaction.atomic():
                DoctorView.objects.create(
                    doctor=doctor,
                    user=user
                )
                Doctor.objects.filter(id=doctor.id).update(
                    view_count=models.F('view_count') + 1
                )
        except IntegrityError:
            pass

        serializer = self.get_serializer(doctor)
        return Response(serializer.data)


class DoctorRatingCreateAPI(generics.CreateAPIView):
    serializer_class = DoctorRatingSerializer
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













# Doctor Consultation VIEWS


class DoctorConsultationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Doctor's consultation management

    Endpoints:
    - GET /api/doctor/consultations/             - List all consultations
    - GET /api/doctor/consultations/new/         - New consultations (paid, not accepted)
    - GET /api/doctor/consultations/active/      - Active (accepted, in_progress)
    - GET /api/doctor/consultations/completed/   - Completed consultations
    - GET /api/doctor/consultations/{id}/        - Consultation detail
    - POST /api/doctor/consultations/{id}/accept/ - Accept and create chat room
    - POST /api/doctor/consultations/{id}/complete/ - Mark as completed
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ConsultationDetailSerializer

    def get_queryset(self):
        """Get consultations for current doctor"""
        user = self.request.user

        # Faqat doctorlar kirishi mumkin
        if user.role != 'doctor':
            return ConsultationRequest.objects.none()

        return ConsultationRequest.objects.filter(
            doctor=user
        ).select_related(
            'client',
            'doctor',
            'availability_slot',
            'chat_room'
        ).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def new(self, request):
        """
        Yangi konsultatsiyalar (to'langan, hali qabul qilinmagan)

        GET /api/doctor/consultations/new/

        Query Parameters:
        - date: Specific date (YYYY-MM-DD) - Aniq sana
        - start_date: From date (YYYY-MM-DD) - Boshlanish sanasi
        - end_date: To date (YYYY-MM-DD) - Tugash sanasi
        - filter: 'today' | 'future' | 'all' - Tezkor filter

        Examples:
        - /new/ - Bugun va kelajak (default)
        - /new/?filter=today - Faqat bugun
        - /new/?filter=future - Faqat kelajak
        - /new/?filter=all - Hammasi (o'tmish ham)
        - /new/?date=2026-02-10 - Aniq sana
        - /new/?start_date=2026-02-07&end_date=2026-02-14 - Oraliq
        """
        from datetime import date, datetime

        today = date.today()

        # Base queryset
        consultations = self.get_queryset().filter(status='paid')

        # Get filter parameters
        filter_type = request.query_params.get('filter')
        specific_date = request.query_params.get('date')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Apply filters
        if specific_date:
            # Aniq sana
            try:
                target_date = datetime.strptime(specific_date, '%Y-%m-%d').date()
                consultations = consultations.filter(requested_date=target_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif start_date or end_date:
            # Sana oralig'i
            try:
                if start_date:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    consultations = consultations.filter(requested_date__gte=start)

                if end_date:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    consultations = consultations.filter(requested_date__lte=end)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif filter_type:
            # Tezkor filterlar
            if filter_type == 'today':
                consultations = consultations.filter(requested_date=today)
            elif filter_type == 'future':
                consultations = consultations.filter(requested_date__gt=today)
            elif filter_type == 'all':
                # Hammasi - hech qanday sana filteri yo'q
                pass
            else:
                return Response(
                    {'error': 'Invalid filter type. Use: today, future, all'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        else:
            # Default: bugun va kelajak
            consultations = consultations.filter(requested_date__gte=today)

        # Order by date and time
        consultations = consultations.order_by('requested_date', 'requested_time')

        serializer = self.get_serializer(consultations, many=True)
        return Response({
            'count': consultations.count(),
            'results': serializer.data,
            'filter_applied': {
                'filter': filter_type,
                'date': specific_date,
                'start_date': start_date,
                'end_date': end_date,
                'default': 'today and future' if not any([filter_type, specific_date, start_date, end_date]) else None
            }
        })


    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Active konsultatsiyalar (accepted, in_progress)

        GET /api/doctor/consultations/active/
        """
        consultations = self.get_queryset().filter(
            status__in=['accepted', 'in_progress']
        )

        serializer = self.get_serializer(consultations, many=True)
        return Response({
            'count': consultations.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """
        Tugatilgan konsultatsiyalar

        GET /api/doctor/consultations/completed/
        """
        consultations = self.get_queryset().filter(
            status='completed'
        )

        serializer = self.get_serializer(consultations, many=True)
        return Response({
            'count': consultations.count(),
            'results': serializer.data
        })

    # Accept metodini yangilang:
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Konsultatsiyani qabul qilish va chat room yaratish
        """
        import logging
        logger = logging.getLogger(__name__)

        consultation = self.get_object()

        if consultation.doctor != request.user:
            return Response(
                {'error': 'This is not your consultation'},
                status=status.HTTP_403_FORBIDDEN
            )

        if consultation.status != 'paid':
            return Response(
                {'error': f'Cannot accept consultation with status {consultation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Accept qilish
        try:
            consultation.accept()
            logger.info(f"✅ Consultation {consultation.id} accepted by doctor {request.user.id}")
        except Exception as e:
            logger.error(f"❌ Failed to accept consultation {consultation.id}: {e}")
            return Response(
                {'error': f'Failed to accept consultation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Notifications
        try:
            self._notify_client_acceptance(consultation)
            logger.info(f"✅ Client notification sent for consultation {consultation.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send client notification: {e}")

        try:
            self._notify_telegram_acceptance(consultation)
            logger.info(f"✅ Telegram notification sent for consultation {consultation.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}")

        return Response({
            'consultation_id': consultation.id,
            'status': consultation.status,
            'chat_room': {
                'id': consultation.chat_room.id,
            } if consultation.chat_room else None,
            'message': 'Consultation accepted and chat room created'
        })

    # Complete metodini yangilang:
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Konsultatsiyani tugatish
        """
        import logging
        logger = logging.getLogger(__name__)

        consultation = self.get_object()

        if consultation.doctor != request.user:
            return Response(
                {'error': 'This is not your consultation'},
                status=status.HTTP_403_FORBIDDEN
            )

        if consultation.status not in ['accepted', 'in_progress']:
            return Response(
                {'error': f'Cannot complete consultation with status {consultation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Tugatish
        try:
            consultation.complete()
            logger.info(f"✅ Consultation {consultation.id} completed by doctor {request.user.id}")
        except Exception as e:
            logger.error(f"❌ Failed to complete consultation {consultation.id}: {e}")
            return Response(
                {'error': f'Failed to complete consultation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Chat roomni deactivate
        if consultation.chat_room:
            try:
                consultation.chat_room.is_active = False
                consultation.chat_room.save()
                logger.info(f"✅ Chat room {consultation.chat_room.id} deactivated")
            except Exception as e:
                logger.warning(f"⚠️ Could not deactivate chat room: {e}")

        # Notifications
        try:
            self._notify_client_completion(consultation)
            logger.info(f"✅ Client completion notification sent for consultation {consultation.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send client completion notification: {e}")

        try:
            self._notify_telegram_completion(consultation)
            logger.info(f"✅ Telegram completion notification sent for consultation {consultation.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram completion notification: {e}")

        return Response({
            'consultation_id': consultation.id,
            'status': consultation.status,
            'completed_at': consultation.completed_at,
            'message': 'Consultation completed successfully'
        })

    def _notify_client_acceptance(self, consultation):
        """
        Clientga konsultatsiya qabul qilingani haqida xabar yuborish
        """
        from utils.fcm import send_fcm
        import logging

        logger = logging.getLogger(__name__)

        logger.info(f"📤 Sending acceptance FCM to client {consultation.client.id}")

        try:
            send_fcm(
                user=consultation.client,
                type='consultation_accepted',
                title='Konsultatsiya qabul qilindi',
                body=f'Dr. {consultation.doctor.first_name or "Doctor"} sizning konsultatsiyangizni qabul qildi',
                consultation_id=consultation.id,
                doctor_id=consultation.doctor.id,
                doctor_name=consultation.doctor.first_name or 'Doctor',
                chat_room_id=consultation.chat_room.id if consultation.chat_room else None,
            )
            logger.info(f"✅ Acceptance FCM sent successfully to client {consultation.client.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send acceptance FCM to client {consultation.client.id}: {e}")
            raise

    def _notify_client_completion(self, consultation):
        """
        Clientga konsultatsiya tugatilgani haqida xabar yuborish
        """
        from utils.fcm import send_fcm
        import logging

        logger = logging.getLogger(__name__)

        logger.info(f"📤 Sending completion FCM to client {consultation.client.id}")

        try:
            send_fcm(
                user=consultation.client,
                type='consultation_completed',
                title='Konsultatsiya tugatildi',
                body=f'Dr. {consultation.doctor.first_name or "Doctor"} bilan konsultatsiyangiz yakunlandi',
                consultation_id=consultation.id,
                doctor_id=consultation.doctor.id,
                doctor_name=consultation.doctor.first_name or 'Doctor',
            )
            logger.info(f"✅ Completion FCM sent successfully to client {consultation.client.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send completion FCM to client {consultation.client.id}: {e}")
            raise

    def _notify_telegram_acceptance(self, consultation):
        """
        Telegram botga doctor qabul qilgani haqida xabar
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            doctor = Doctor.objects.get(user=consultation.doctor)
            doctor_name = doctor.full_name
        except:
            doctor_name = consultation.doctor.first_name or "Unknown"

        message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━
✅ KONSULTATSIYA QABUL QILINDI #{consultation.id}
━━━━━━━━━━━━━━━━━━━━━━━━

🏥 Doctor: {doctor_name}
🆔 Doctor User ID: {consultation.doctor.id}

👤 Client: {consultation.client.first_name or 'Ism yoq'} {consultation.client.last_name or ''}
📞 Telefon: {consultation.client.phone}
🆔 Client User ID: {consultation.client.id}

📅 Sana: {consultation.requested_date.strftime('%d.%m.%Y')}
🕐 Vaqt: {consultation.requested_time.strftime('%H:%M')}

💬 Chat Room ID: {consultation.chat_room.id if consultation.chat_room else 'N/A'}
✅ Status: ACCEPTED
━━━━━━━━━━━━━━━━━━━━━━━━
"""

        logger.info(f"📤 Telegram ACCEPTANCE notification:\n{message}")

        # TODO: Telegram botga yuborish
        from utils.telegram import send_to_bot
        send_to_bot(message)

    def _notify_telegram_completion(self, consultation):
        """
        Telegram botga konsultatsiya tugatilgani haqida xabar
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            doctor = Doctor.objects.get(user=consultation.doctor)
            doctor_name = doctor.full_name
        except:
            doctor_name = consultation.doctor.first_name or "Unknown"

        # Davomiylikni hisoblash
        duration = "N/A"
        if consultation.accepted_at and consultation.completed_at:
            delta = consultation.completed_at - consultation.accepted_at
            minutes = int(delta.total_seconds() / 60)
            duration = f"{minutes} minut"

        message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━
✅ KONSULTATSIYA TUGATILDI #{consultation.id}
━━━━━━━━━━━━━━━━━━━━━━━━

🏥 Doctor: {doctor_name}
🆔 Doctor User ID: {consultation.doctor.id}

👤 Client: {consultation.client.first_name or 'Ism yoq'} {consultation.client.last_name or ''}
📞 Telefon: {consultation.client.phone}
🆔 Client User ID: {consultation.client.id}

📅 Sana: {consultation.requested_date.strftime('%d.%m.%Y')}
🕐 Vaqt: {consultation.requested_time.strftime('%H:%M')}

⏱️ Davomiyligi: {duration}
✅ Status: COMPLETED
━━━━━━━━━━━━━━━━━━━━━━━━
"""

        logger.info(f"📤 Telegram COMPLETION notification:\n{message}")

        # TODO: Telegram botga yuborish
        from utils.telegram import send_to_bot
        send_to_bot(message)

















