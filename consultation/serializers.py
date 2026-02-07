from rest_framework import serializers

from specialist.models import Doctor
from .models import ConsultationRequest, DoctorAvailability


class ConsultationRequestSerializer(serializers.ModelSerializer):
    """
    Client uchun konsultatsiya serializer
    """

    # Doctor ma'lumotlari
    doctor_id = serializers.IntegerField(source='doctor.id', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    doctor_avatar = serializers.SerializerMethodField()
    doctor_type = serializers.SerializerMethodField()

    # Vaqt ma'lumotlari
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    # Chat room
    chat_room_id = serializers.IntegerField(source='chat_room.id', read_only=True, allow_null=True)
    chat_room_active = serializers.BooleanField(source='chat_room.is_active', read_only=True, allow_null=True)

    # Status info
    is_paid = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = ConsultationRequest
        fields = [
            'id',
            'doctor_id',
            'doctor_name',
            'doctor_avatar',
            'doctor_type',
            'date',
            'time',
            'reason',
            'notes',
            'status',
            'is_paid',
            'can_cancel',
            'chat_room_id',
            'chat_room_active',
            'created_at',
            'paid_at',
            'accepted_at',
            'started_at',
            'completed_at',
        ]

    def get_client_name(self, obj):
        """Client nomi"""
        first_name = obj.client.first_name or ''
        last_name = obj.client.last_name or ''
        full_name = f"{first_name} {last_name}".strip()

        # Agar to'liq ism bo'lmasa
        if not full_name:
            # Telefon raqam o'rniga "Mijoz" yoki formatted phone
            phone = obj.client.phone or ''
            if phone:
                # +998 XX XXX XX XX formatida
                if phone.startswith('998') and len(phone) >= 12:
                    return f"+{phone[:3]} {phone[3:5]} {phone[5:8]} {phone[8:10]} {phone[10:]}"
                return f"+{phone}"
            return "Mijoz"  # Default

        return full_name

    def get_client_avatar(self, obj):
        """Client avatar URL (to'liq URL)"""
        if hasattr(obj.client, 'avatar') and obj.client.avatar:
            # Request context orqali to'liq URL yaratish
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.client.avatar.url)
            # Yoki faqat URL
            return obj.client.avatar.url
        return None

    def get_doctor_type(self, obj):
        try:
            doctor = Doctor.objects.get(user=obj.doctor)
            if doctor.type_doctor:
                # Enum bo'lsa
                if hasattr(doctor.type_doctor, 'value'):
                    return doctor.type_doctor.value  # ← "Terapevt"
                # String ga aylantirish
                return str(doctor.type_doctor)  # ← "Terapevt"
        except:
            pass
        return None

    def get_date(self, obj):
        """Konsultatsiya sanasi"""
        if obj.availability_slot:
            return obj.availability_slot.date.strftime('%Y-%m-%d')
        return obj.requested_date.strftime('%Y-%m-%d')

    def get_time(self, obj):
        """Konsultatsiya vaqti"""
        if obj.availability_slot:
            start = obj.availability_slot.start_time.strftime('%H:%M')
            end = obj.availability_slot.end_time.strftime('%H:%M')
            return f"{start} - {end}"
        return obj.requested_time.strftime('%H:%M')

    def get_is_paid(self, obj):
        """To'langanmi?"""
        return obj.status in ['paid', 'accepted', 'in_progress', 'completed']

    def get_can_cancel(self, obj):
        """Bekor qilish mumkinmi?"""
        return obj.status not in ['completed', 'cancelled']


class ConsultationListSerializer(serializers.ModelSerializer):
    """
    Qisqa ma'lumot (list uchun)
    """

    doctor_name = serializers.SerializerMethodField()
    doctor_type = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    class Meta:
        model = ConsultationRequest
        fields = [
            'id',
            'doctor_name',
            'doctor_type',
            'date',
            'time',
            'status',
            'reason',
            'created_at',
        ]

    def get_doctor_name(self, obj):
        try:
            doctor = Doctor.objects.get(user=obj.doctor)
            return doctor.full_name
        except:
            return obj.doctor.first_name or obj.doctor.phone

    def get_doctor_type(self, obj):
        try:
            doctor = Doctor.objects.get(user=obj.doctor)
            return doctor.type_doctor
        except:
            return None

    def get_date(self, obj):
        if obj.availability_slot:
            return obj.availability_slot.date.strftime('%Y-%m-%d')
        return obj.requested_date.strftime('%Y-%m-%d')

    def get_time(self, obj):
        if obj.availability_slot:
            start = obj.availability_slot.start_time.strftime('%H:%M')
            end = obj.availability_slot.end_time.strftime('%H:%M')
            return f"{start} - {end}"
        return obj.requested_time.strftime('%H:%M')


class ConsultationCreateSerializer(serializers.Serializer):
    """
    Client faqat slot ID tanlaydi

    Example:
    {
        "slot_id": 123,
        "reason": "Bosh og'rig'i"  (ixtiyoriy)
    }
    """
    slot_id = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_slot_id(self, value):
        """Validate slot exists and is available"""
        try:
            slot = DoctorAvailability.objects.select_related('doctor').get(id=value)

            if not slot.is_available:
                raise serializers.ValidationError("This time slot is already booked")

            # Check doctor is verified
            try:
                doctor = Doctor.objects.get(user=slot.doctor)
                if not doctor.is_verified or not doctor.user.is_approved:
                    raise serializers.ValidationError("Doctor is not available")
            except Doctor.DoesNotExist:
                raise serializers.ValidationError("Doctor not found")

            return value

        except DoctorAvailability.DoesNotExist:
            raise serializers.ValidationError("Time slot not found")


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    """Doctor availability slot serializer"""

    doctor_name = serializers.CharField(source='doctor.first_name', read_only=True)
    is_booked = serializers.SerializerMethodField()

    class Meta:
        model = DoctorAvailability
        fields = [
            'id', 'doctor', 'doctor_name',
            'date', 'start_time', 'end_time',
            'is_available', 'is_booked',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_is_booked(self, obj):
        return not obj.is_available










