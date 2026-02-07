from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, timedelta
from .models import ConsultationRequest, DoctorAvailability
from .serializers import ConsultationRequestSerializer



class ConsultationViewSet(viewsets.ModelViewSet):
    """
    Consultation management

    Endpoints:
    - GET    /api/consultations/              - List my consultations
    - POST   /api/consultations/create/       - Create consultation request
    - GET    /api/consultations/{id}/         - Get consultation detail
    - POST   /api/consultations/{id}/accept/  - Doctor accepts (doctor only)
    - POST   /api/consultations/{id}/complete/ - Mark completed
    - POST   /api/consultations/{id}/cancel/  - Cancel

    - GET    /api/consultations/available-slots/ - Get available time slots
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ConsultationRequestSerializer

    def get_queryset(self):
        """Get consultations for current user"""
        user = self.request.user

        if user.role == 'doctor':
            return ConsultationRequest.objects.filter(doctor=user)
        else:
            return ConsultationRequest.objects.filter(client=user)

    @action(detail=False, methods=['get'])
    def availability(self, request):
        """
        Get doctor availability for date range

        GET /api/consultations/availability/?doctor_id=5&start_date=2024-12-08&end_date=2024-12-15

        Note: doctor_id is the Doctor MODEL id, not User id
        Returns both doctor_user_id and doctor_profile_id for clarity
        """
        from specialist.models import Doctor

        doctor_id = request.query_params.get('doctor_id')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not doctor_id:
            return Response(
                {'error': 'doctor_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = Doctor.objects.select_related('user').get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Default: today + 7 days
        start_date = date.fromisoformat(start_date_str) if start_date_str else date.today()
        end_date = date.fromisoformat(end_date_str) if end_date_str else (start_date + timedelta(days=6))

        # Get availability
        availability_slots = DoctorAvailability.objects.filter(
            doctor=doctor.user,
            date__gte=start_date,
            date__lte=end_date,
            template__is_active=True
        ).select_related('consultation', 'consultation__client').order_by('date', 'start_time')

        # Group by date
        result = {}
        for slot in availability_slots:
            date_key = slot.date.isoformat()

            if date_key not in result:
                result[date_key] = {
                    'date': date_key,
                    'day_name': slot.date.strftime('%A'),
                    'slots': []
                }

            slot_data = {
                'id': slot.id,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'is_available': slot.is_available,
            }

            if not slot.is_available and slot.consultation:
                slot_data['booked_by'] = f"Client #{slot.consultation.client.id}"

            result[date_key]['slots'].append(slot_data)

        return Response({
            'doctor_user_id': doctor.user.id,  # ← User model ID (consistent)
            # 'doctor_profile_id': doctor.id,  # ← Doctor model ID
            'doctor_name': doctor.full_name,
            'availability': list(result.values())
        })

    @action(detail=False, methods=['post'])
    def create_consultation(self, request):
        """
        Create consultation by selecting a slot

        YANGI MANTIQ: Client DOIM muvaffaqiyatli yoziladi

        POST /api/consultations/create_consultation/
        {
            "slot_id": 123,
            "reason": "Bosh og'rig'i" (optional)
        }
        """
        from specialist.models import Doctor
        import logging
        logger = logging.getLogger(__name__)

        slot_id = request.data.get('slot_id')
        reason = request.data.get('reason', '')

        if not slot_id:
            return Response(
                {'error': 'slot_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find availability slot
        try:
            availability_slot = DoctorAvailability.objects.select_related(
                'doctor', 'consultation', 'consultation__client'
            ).get(id=slot_id)
        except DoctorAvailability.DoesNotExist:
            return Response(
                {'error': 'Time slot does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get doctor info
        try:
            doctor = Doctor.objects.get(user=availability_slot.doctor)
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if doctor is verified
        if not doctor.is_verified or not doctor.user.is_approved:
            return Response(
                {'error': 'Doctor is not available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ YANGI: Slot statusini tekshirish (band yoki bo'sh)
        slot_was_available = availability_slot.is_available

        # ✅ Create consultation (DOIM yaratiladi - slot band bo'lsa ham)
        consultation = ConsultationRequest.objects.create(
            client=request.user,
            doctor=availability_slot.doctor,
            requested_date=availability_slot.date,
            requested_time=availability_slot.start_time,
            availability_slot=availability_slot,
            reason=reason,
            status='created'
        )

        # Agar slot bo'sh bo'lsa - avtomatik book qilish
        if slot_was_available:
            # Slotni band qilish
            availability_slot.book(consultation)
            logger.info(f"✅ Slot {slot_id} booked for consultation {consultation.id}")
        else:
            # Slot band - lekin konsultatsiya yaratildi (navbatda)
            logger.warning(
                f"⚠️ Slot {slot_id} already booked, but consultation {consultation.id} created anyway. "
                f"Slot was booked by consultation {availability_slot.consultation.id if availability_slot.consultation else 'Unknown'}"
            )

        # Mark as paid (for testing)
        consultation.mark_as_paid()

        # 📱 NOTIFICATIONS

        if slot_was_available:
            # ✅ Slot bo'sh edi - muvaffaqiyatli
            self._send_consultation_notifications(consultation)
            logger.info(f"✅ Success notifications sent for consultation {consultation.id}")
        else:
            # ⚠️ Slot band edi - yangi konsultatsiya (navbat)
            # Doctor FCM yuboramiz (yangi konsultatsiya haqida)
            self._send_consultation_notifications(consultation)

            # Telegram botga alohida xabar (slot band edi)
            self._send_telegram_success_booking(
                consultation=consultation,
                doctor=doctor,
                slot=availability_slot
            )
            logger.warning(f"⚠️ Slot occupied notification sent for consultation {consultation.id}")

        return Response({
            'consultation_id': consultation.id,
            'status': consultation.status,
            'doctor': {
                'id': doctor.id,
                'name': doctor.full_name,
                'price': float(doctor.consultation_price),
            },
            'date': str(availability_slot.date),
            'time': f"{availability_slot.start_time.strftime('%H:%M')} - {availability_slot.end_time.strftime('%H:%M')}",
            'slot_was_available': slot_was_available,
            'message': 'Konsultatsiya muvaffaqiyatli yaratildi' if slot_was_available else 'Konsultatsiya yaratildi'
        }, status=status.HTTP_201_CREATED)

    def _send_telegram_success_booking(self, consultation, doctor, slot):
        """
        ⚠️ Slot band bo'lganda yangi konsultatsiya yaratilganini bildirish

        Bu holat: Client yozildi, lekin slot allaqachon band edi
        """
        import logging
        logger = logging.getLogger(__name__)

        doctor_name = doctor.full_name if doctor else "Unknown Doctor"
        doctor_user_id = doctor.user.id if doctor else "N/A"
        doctor_type = doctor.type_doctor if doctor else "N/A"

        # # Kim tomonidan band qilingan
        # booked_by = "Unknown"
        # booked_by_id = "N/A"
        # if slot.consultation and slot.consultation.client:
        #     booked_by = f"{slot.consultation.client.first_name or 'Ism yoq'} {slot.consultation.client.last_name or ''}"
        #     booked_by_id = slot.consultation.client.id

        message = f"""
    ━━━━━━━━━━━━━━━━━━━━━━━━
    ⚠️ NAVBATGA YOZILDI (Slot band edi)
    ━━━━━━━━━━━━━━━━━━━━━━━━

    📋 Konsultatsiya ID: #{consultation.id}
    ✅ Status: YARATILDI

    👤 Yangi Mijoz:
    👤 Ism: {consultation.client.first_name or 'Ism yoq'} {consultation.client.last_name or ''}
    📞 Telefon: +{consultation.client.phone}
    🆔 Client User ID: {consultation.client.id}

    🏥 Doctor Name: {doctor_name}
    🆔 Doctor User ID: {doctor_user_id}
    🏥 Doctor Type: {doctor_type}

    📅 Sana: {slot.date.strftime('%d.%m.%Y')}
    🕐 Vaqt: {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}

    💰 Narx: {doctor.consultation_price:,.0f} so'm
    💬 Sabab: {consultation.reason or 'Sabab korsatilmagan'}

    ⚠️ ESLATMA: Bu vaqt allaqachon band!

    ℹ️ Yangi konsultatsiya yaratildi, lekin navbatda
    ━━━━━━━━━━━━━━━━━━━━━━━━
    """

        logger.warning(f"📤 Telegram SLOT OCCUPIED notification:\n{message}")

        try:
            from utils.telegram import send_to_bot
            send_to_bot(message)
            logger.info(f"✅ Telegram slot occupied notification sent")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}")

    def _send_consultation_notifications(self, consultation):
        """
        ✅ MUVAFFAQIYATLI YOZILGANDA

        Send notifications to:
        1. Doctor (FCM)
        2. Telegram Bot (operator)
        """
        from utils.fcm import send_fcm
        import logging

        logger = logging.getLogger(__name__)

        # 1. Notify Doctor (FCM)
        try:
            send_fcm(
                user=consultation.doctor,
                type='new_consultation',
                title='Yangi Konsultatsiya',
                body=f'{consultation.client.first_name or consultation.client.phone} konsultatsiya uchun yozildi',
                consultation_id=consultation.id,
                client_id=consultation.client.id,
                client_name=consultation.client.first_name or consultation.client.phone,
                client_phone=consultation.client.phone,
                requested_date=str(consultation.requested_date),
                requested_time=str(consultation.requested_time),
                reason=consultation.reason,
            )
            logger.info(f"✅ FCM sent to doctor {consultation.doctor.id}")
        except Exception as e:
            logger.error(f"❌ Failed to send FCM to doctor: {e}")

        # 2. Notify Bot (Telegram) - MUVAFFAQIYATLI
        try:
            self._send_telegram_success_booking(consultation)
            logger.info(f"✅ Telegram (success) sent to bot")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram: {e}")

#     def _send_telegram_success_booking(self, consultation):
#         """
#         ✅ MUVAFFAQIYATLI YOZILGANDA Telegram botga yuborish
#         """
#         import logging
#         logger = logging.getLogger(__name__)
#
#         try:
#             doctor = Doctor.objects.get(user=consultation.doctor)
#             doctor_name = doctor.full_name
#             doctor_price = doctor.consultation_price
#             doctor_type = doctor.type_doctor if doctor else "N/A"
#         except:
#             doctor_name = consultation.doctor.first_name or "Unknown"
#             doctor_price = 0
#
#         message = f"""
# ━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ YANGI KONSULTATSIYA #{consultation.id}
# ━━━━━━━━━━━━━━━━━━━━━━━━
#
# 👤 Mijoz: {consultation.client.first_name or 'Ism yoq'} {consultation.client.last_name or ''}
# 📞 Telefon: +{consultation.client.phone}
# 🆔 Client User ID: {consultation.client.id}
#
# 🏥 Doctor: {doctor_name}
# 🆔 Doctor User ID: {consultation.doctor.id}
# 🏥 Doctor Type: {doctor_type}
#
# 📅 Sana: {consultation.requested_date.strftime('%d.%m.%Y')}
# 🕐 Vaqt: {consultation.requested_time.strftime('%H:%M')}
#
# 💰 Narx: {doctor_price:,.0f} so'm
# ✅ Status: PAID (To'langan)
#
# 💬 Sabab: {consultation.reason or 'Sabab korsatilmagan'}
# ━━━━━━━━━━━━━━━━━━━━━━━━
# """
#
#         logger.info(f"📤 Telegram SUCCESS notification:\n{message}")
#
#         # TODO: Telegram botga yuborish
#         from utils.telegram import send_to_bot
#         send_to_bot(message)

    # def _send_telegram_notification(self, consultation):
    #     """
    #     DEPRECATED: Use _send_telegram_success_booking instead
    #     """
    #     self._send_telegram_success_booking(consultation)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Doctor accepts consultation

        POST /api/consultations/{id}/accept/
        """
        consultation = self.get_object()

        # Only doctor can accept
        if consultation.doctor != request.user:
            return Response(
                {'error': 'Only assigned doctor can accept'},
                status=status.HTTP_403_FORBIDDEN
            )

        if consultation.status != 'paid':
            return Response(
                {'error': f'Cannot accept consultation with status {consultation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Accept
        consultation.accept()

        return Response({
            'consultation_id': consultation.id,
            'status': consultation.status,
            'room_id': consultation.chat_room.id if consultation.chat_room else None,
            'message': 'Consultation accepted'
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete consultation

        POST /api/consultations/{id}/complete/
        """
        consultation = self.get_object()

        # Only doctor can complete
        if consultation.doctor != request.user:
            return Response(
                {'error': 'Only doctor can complete'},
                status=status.HTTP_403_FORBIDDEN
            )

        if consultation.status not in ['accepted', 'in_progress']:
            return Response(
                {'error': f'Cannot complete consultation with status {consultation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Complete
        consultation.complete()

        return Response({
            'consultation_id': consultation.id,
            'status': consultation.status,
            'message': 'Consultation completed'
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel consultation

        POST /api/consultations/{id}/cancel/
        """
        consultation = self.get_object()

        # Both client and doctor can cancel
        if consultation.client != request.user and consultation.doctor != request.user:
            return Response(
                {'error': 'Only client or doctor can cancel'},
                status=status.HTTP_403_FORBIDDEN
            )

        if consultation.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel consultation with status {consultation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cancel
        consultation.status = 'cancelled'
        consultation.save()

        # Free the slot
        if consultation.availability_slot:
            consultation.availability_slot.is_available = True
            consultation.availability_slot.consultation = None
            consultation.availability_slot.save()

        return Response({
            'consultation_id': consultation.id,
            'status': consultation.status,
            'message': 'Consultation cancelled'
        })