from django.utils import timezone
from django.db import models
from django.conf import settings


class GlobalAvailabilityTemplate(models.Model):
    """
    Global availability template

    Admin creates ONCE for ALL doctors
    System auto-generates DoctorAvailability for each doctor

    Example:
    - Date: 2024-12-11
    - Time: 09:00-10:00
    - Active: True

    → System creates this slot for ALL approved doctors
    """

    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )

    class Meta:
        db_table = 'global_availability_templates'
        ordering = ['date', 'start_time']
        unique_together = ['date', 'start_time']
        indexes = [
            models.Index(fields=['date', 'is_active']),
        ]

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time}"

    def generate_for_all_doctors(self):
        """
        Generate DoctorAvailability for all approved doctors

        Called automatically after save
        """
        from specialist.models import Doctor

        doctors = Doctor.objects.filter(
            is_verified=True,
            user__is_approved=True,
            user__is_active=True
        ).select_related('user')

        count = 0

        for doctor in doctors:
            obj, created = DoctorAvailability.objects.get_or_create(
                doctor=doctor.user,
                template=self,
                date=self.date,
                start_time=self.start_time,
                defaults={
                    'end_time': self.end_time,
                    'is_available': True
                }
            )

            if created:
                count += 1

        return count

    def save(self, *args, **kwargs):
        """Auto-generate for all doctors on save"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # New template → generate for all doctors
            count = self.generate_for_all_doctors()
            print(f"✅ Auto-generated {count} doctor slots")


class DoctorAvailability(models.Model):
    """
    Doctor-specific availability (auto-generated from template)
    """

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availability_slots',
        limit_choices_to={'role': 'doctor'}
    )

    # Link to template (if created from template)
    template = models.ForeignKey(
        GlobalAvailabilityTemplate,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='doctor_slots'
    )

    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    consultation = models.ForeignKey(
        'ConsultationRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booked_slot'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'doctor_availability'
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date', 'start_time']
        indexes = [
            models.Index(fields=['doctor', 'date', 'is_available']),
            models.Index(fields=['template', 'is_available']),
        ]

    def __str__(self):
        doctor_name = self.doctor.first_name or self.doctor.phone
        return f"{doctor_name} - {self.date} {self.start_time}-{self.end_time}"

    def book(self, consultation):
        """Mark as booked"""
        self.is_available = False
        self.consultation = consultation
        self.save()

    def release(self):
        """Mark as available"""
        self.is_available = True
        self.consultation = None
        self.save()

class ConsultationRequest(models.Model):
    """Consultation request"""

    STATUS_CHOICES = (
        ('created', 'Created'),
        ('payment_pending', 'Payment Pending'),
        ('paid', 'Paid'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations_as_client',
        limit_choices_to={'role': 'client'}
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations_as_doctor',
        limit_choices_to={'role': 'doctor'}
    )

    requested_date = models.DateField(db_index=True)
    requested_time = models.TimeField()

    availability_slot = models.ForeignKey(
        DoctorAvailability,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='consultations'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        db_index=True
    )

    chat_room = models.ForeignKey(
        'chat.ChatRoom',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultation'
    )

    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'consultation_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['doctor', 'requested_date', 'status']),
            models.Index(fields=['client', 'status']),
        ]

    def __str__(self):
        return f"Consultation #{self.id} - {self.client.phone} → Dr. {self.doctor.first_name}"

    @property
    def payment(self):
        """Get paid payment for this consultation"""
        return self.payments.filter(status='paid').first()

    def is_paid(self):
        """Check if consultation is paid"""
        return self.payments.filter(status='paid').exists()


    def mark_as_paid(self):
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()

    def accept(self):
        """
        Doctor konsultatsiyani qabul qiladi va chat room yaratadi yoki aktivlashtiradi

        Status: paid -> accepted

        Logika:
        1. Agar bu konsultatsiyaga room allaqachon biriktirilgan bo'lsa → Aktivlashtirish
        2. Agar doctor va client o'rtasida eski room bo'lsa → Uni qayta ishlatish
        3. Aks holda → Yangi room yaratish
        """
        from chat.models import ChatRoom
        from django.utils import timezone
        import logging

        logger = logging.getLogger(__name__)

        if self.status != 'paid':
            raise ValueError(f"Cannot accept consultation with status {self.status}")

        # 1. Agar chat room allaqachon biriktirilgan bo'lsa
        if self.chat_room:
            logger.info(f"Consultation {self.id} already has room {self.chat_room.id}")

            # Aktivlashtirish (agar deaktiv bo'lsa)
            if not self.chat_room.is_active:
                self.chat_room.is_active = True
                self.chat_room.save()
                logger.info(f"✅ Reactivated room {self.chat_room.id}")

            self.status = 'accepted'
            self.accepted_at = timezone.now()
            self.save()
            return self.chat_room

        # 2. Eski chat room borligini tekshirish (doctor va client o'rtasida)
        logger.info(f"Checking for existing room between doctor {self.doctor.id} and client {self.client.id}")

        try:
            existing_room = ChatRoom.objects.filter(
                room_type='1:1',
                participants=self.doctor
            ).filter(
                participants=self.client
            ).first()

            if existing_room:
                logger.info(f"✅ Found existing room {existing_room.id} between doctor and client")

                # Eski roomni aktivlashtirish
                existing_room.is_active = True
                existing_room.save()

                # Konsultatsiyaga biriktirish
                self.chat_room = existing_room
                self.status = 'accepted'
                self.accepted_at = timezone.now()
                self.save()

                logger.info(f"✅ Reused room {existing_room.id} for consultation {self.id}")
                return existing_room
            else:
                logger.info(f"No existing room found between doctor {self.doctor.id} and client {self.client.id}")
        except Exception as e:
            logger.error(f"❌ Error checking for existing room: {e}")

        # 3. Yangi chat room yaratish
        logger.info(f"Creating new chat room for consultation {self.id}")

        try:
            chat_room = ChatRoom.objects.create(
                room_type='1:1',
                created_by=self.doctor,
                is_active=True
            )

            # Participants qo'shish
            chat_room.participants.add(self.doctor, self.client)

            logger.info(f"✅ Created new room {chat_room.id}, added doctor {self.doctor.id} and client {self.client.id}")
        except Exception as e:
            logger.error(f"❌ Failed to create chat room: {e}")
            raise

        # Konsultatsiyani yangilash
        self.chat_room = chat_room
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()

        logger.info(f"✅ Consultation {self.id} accepted with room {chat_room.id}")
        return chat_room

    # consultation/models.py dagi ConsultationRequest classiga qo'shing

    def complete(self):
        """
        Konsultatsiyani tugatish

        Status: accepted/in_progress -> completed

        Bu method:
        1. Statusni 'completed'ga o'zgartiradi
        2. completed_at vaqtini belgilaydi
        3. Chat roomni deactivate qiladi (optional)
        4. MUHIM: Slotni BO'SHATADI (is_available = True)
        """
        from django.utils import timezone
        import logging

        logger = logging.getLogger(__name__)

        # Faqat accepted yoki in_progress statusdagi konsultatsiyalarni tugatish mumkin
        if self.status not in ['accepted', 'in_progress']:
            raise ValueError(f"Cannot complete consultation with status {self.status}")

        # Statusni yangilash
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

        # Chat roomni deactivate qilish (optional)
        if self.chat_room:
            try:
                self.chat_room.is_active = False
                self.chat_room.save()
                logger.info(f"Chat room {self.chat_room.id} deactivated")
            except Exception as e:
                logger.warning(f"Could not deactivate chat room: {e}")

        # ✅ MUHIM: Slotni BO'SHATISH
        if self.availability_slot:
            try:
                self.availability_slot.is_available = True
                self.availability_slot.consultation = None
                self.availability_slot.save()
                logger.info(f"✅ Freed availability slot {self.availability_slot.id}")
            except Exception as e:
                logger.error(f"❌ Could not free slot: {e}")

        logger.info(f"✅ Consultation {self.id} completed")

        return True

    def can_client_book_again(self, client):
        """
        Clientning yana booking qilishi mumkinmi?

        Args:
            client: UserModel instance

        Returns:
            bool: True - booking qilishi mumkin, False - mumkin emas
            str: Sabab (agar False bo'lsa)

        Usage:
            can_book, reason = consultation.can_client_book_again(client)
            if not can_book:
                return Response({'error': reason}, status=400)
        """

        # Agar bu konsultatsiya tugallanmagan bo'lsa
        if self.status not in ['completed', 'cancelled']:
            if self.client == client:
                return False, "Sizning aktiv konsultatsiyangiz mavjud. Avval uni tugatish kerak."

        # Client yana booking qilishi mumkin
        return True, None

    def delete(self, *args, **kwargs):
        """O'chirishdan oldin slotni bo'shatish"""
        if self.availability_slot:
            self.availability_slot.is_available = True
            self.availability_slot.consultation = None
            self.availability_slot.save()
        super().delete(*args, **kwargs)


