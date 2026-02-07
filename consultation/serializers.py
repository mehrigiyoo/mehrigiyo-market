from rest_framework import serializers

from specialist.models import Doctor
from .models import ConsultationRequest, DoctorAvailability


class ConsultationRequestSerializer(serializers.ModelSerializer):
    """Consultation request serializer"""

    client_name = serializers.CharField(source='client.full_name', read_only=True)
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    doctor_avatar = serializers.SerializerMethodField()

    is_paid = serializers.BooleanField(read_only=True)

    # Slot ma'lumotlari
    slot_date = serializers.DateField(source='availability_slot.date', read_only=True)
    slot_start_time = serializers.TimeField(source='availability_slot.start_time', read_only=True)
    slot_end_time = serializers.TimeField(source='availability_slot.end_time', read_only=True)

    class Meta:
        model = ConsultationRequest
        fields = [
            'id', 'client', 'client_name', 'client_phone',
            'doctor', 'doctor_name', 'doctor_avatar',
            'requested_date', 'requested_time',
            'slot_date', 'slot_start_time', 'slot_end_time',
            'status', 'is_paid', 'reason',
            'created_at', 'paid_at', 'accepted_at', 'completed_at'
        ]
        read_only_fields = ['id', 'client', 'created_at']

    def get_doctor_avatar(self, obj):
        if obj.doctor.avatar:
            return obj.doctor.avatar.url
        return None


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










