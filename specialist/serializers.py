from django.db import IntegrityError
from rest_framework import serializers

from account.models import UserModel
from config.validators import normalize_phone
from consultation.models import ConsultationRequest
from .models import Doctor, TypeDoctor, RateDoctor, Advertising, AdviceTime, WorkSchedule, DoctorUnavailable, \
    DoctorVerification, DoctorRating


class AdvertisingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertising
        fields = ['id', 'image', 'title', 'text', 'doctor']

class TypeDoctorSerializer(serializers.ModelSerializer):
    doctors_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TypeDoctor
        fields = ['id', 'name', 'name_uz', 'name_ru', 'name_en', 'image', 'doctors_count']

class RateInfoSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = RateDoctor
        fields = ('id', 'user_name', 'rate', 'feedback', 'created_at')


class DoctorListSerializer(serializers.ModelSerializer):
    type_doctor = TypeDoctorSerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    stars = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = (
            'id', 'full_name', 'image', 'experience',
            'type_doctor', 'average_rating', 'rating_count', 'top', 'stars'
        )

    def get_average_rating(self, obj):
        rating = getattr(obj, 'calculated_average_rating', 0) or 0
        return round(rating, 2)

    def get_rating_count(self, obj):
        return getattr(obj, 'calculated_rating_count', 0)

    def get_stars(self, obj):
        rating = getattr(obj, 'calculated_average_rating', 0) or 0
        stars = []
        for i in range(1, 6):
            if rating >= i:
                stars.append(1)
            elif rating + 0.5 >= i:
                stars.append(0.5)
            else:
                stars.append(0)
        return stars


class DoctorDetailSerializer(serializers.ModelSerializer):
    type_doctor = TypeDoctorSerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    stars = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = (
            'id', 'full_name', 'image', 'experience', 'consultation_price', 'description',
            'type_doctor', 'average_rating', 'rating_count',
            'view_count', 'top', 'birthday', 'gender', 'stars'
        )

    def get_average_rating(self, obj):
        rating = getattr(obj, 'calculated_average_rating', 0) or 0
        return round(rating, 2)

    def get_rating_count(self, obj):
        return getattr(obj, 'calculated_rating_count', 0)

    def get_stars(self, obj):
        rating = getattr(obj, 'calculated_average_rating', 0) or 0
        stars = []
        for i in range(1, 6):
            if rating >= i:
                stars.append(1)
            elif rating + 0.5 >= i:
                stars.append(0.5)
            else:
                stars.append(0)
        return stars

class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = (
            'id',
            'image',
            'full_name',
            'experience',
            'description',
            'type_doctor',
            'birthday',
            'gender',
        )



class DoctorRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    full_name = serializers.CharField()
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')])
    birthday = serializers.DateField(required=False)
    experience = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    type_doctor = serializers.IntegerField()

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Parollar mos emas")

        phone = normalize_phone(attrs['phone'])
        if UserModel.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro‘yxatdan o‘tgan")

        # type_doctor tekshirish
        type_id = attrs.get('type_doctor')
        if not TypeDoctor.objects.filter(id=type_id).exists():
            raise serializers.ValidationError({"type_doctor": "Bunday doctor type mavjud emas."})

        attrs['phone'] = phone
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')

        phone = validated_data.pop('phone')

        # User yaratamiz
        user = UserModel.objects.create_user(
            phone=phone,
            password=password,
            role=UserModel.Roles.DOCTOR,
            is_active=True,        # SMS tasdiqlangan
            is_approved=False      # ADMIN hali tasdiqlamagan
        )

        # Doctor profile
        try:
            doctor = Doctor.objects.create(
                user=user,
                full_name=validated_data['full_name'],
                gender=validated_data['gender'],
                birthday=validated_data.get('birthday'),
                experience=validated_data['experience'],
                description=validated_data.get('description', ''),
                type_doctor_id=validated_data['type_doctor'],
                is_verified=False
            )
        except IntegrityError:
            user.delete()  # user ni ham o'chiramiz, chunki doctor bo'lmadi
            raise serializers.ValidationError({"type_doctor": "Bunday doctor type mavjud emas."})

        # Verification (pending)
        DoctorVerification.objects.create(
            doctor=doctor,
            status='pending'
        )

        return doctor


class DoctorRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorRating
        fields = ('id', 'doctor', 'rating', 'comment')

    def create(self, validated_data):
        user = self.context['request'].user
        doctor = validated_data['doctor']

        rating_obj, _ = DoctorRating.objects.update_or_create(
            doctor=doctor,
            user=user,
            defaults={
                'rating': validated_data['rating'],
                'comment': validated_data.get('comment', '')
            }
        )
        return rating_obj

class WorkScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSchedule
        fields = ['id', 'weekday', 'start_time', 'end_time']

class DoctorUnavailableSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorUnavailable
        fields = ['id', 'date']

class AdviceTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdviceTime
        fields = ['id', 'doctor', 'client', 'start_time', 'end_time']

class AvailableSlotSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()



# class AdvicecDocSerializer(serializers.Serializer):
#     start_time = serializers.DateTimeField()
#     end_time = serializers.DateTimeField()
#     id = serializers.IntegerField()
#
#
# class AdviceSerializer(serializers.ModelSerializer):
#     doctor = DoctorSerializer(read_only=True)
#     doctor_id = serializers.PrimaryKeyRelatedField(
#         queryset=Doctor.objects.all(),
#         source='doctor',
#         write_only=True
#     )
#
#     class Meta:
#         model = AdviceTime
#         fields = '__all__'



# Doctor gender analize serializers

class GenderStatisticsSerializer(serializers.Serializer):
    total_doctors = serializers.IntegerField()
    male_percentage = serializers.FloatField()
    female_percentage = serializers.FloatField()
    male_count = serializers.IntegerField()
    female_count = serializers.IntegerField()










# Doctor Consultation SERIALIZERS


from rest_framework import serializers
from specialist.models import Doctor


class ConsultationDetailSerializer(serializers.ModelSerializer):
    """
    Doctor uchun batafsil konsultatsiya ma'lumoti
    """

    client_id = serializers.IntegerField(source='client.id', read_only=True)
    client_name = serializers.SerializerMethodField()
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    client_avatar = serializers.SerializerMethodField()

    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    chat_room_id = serializers.IntegerField(source='chat_room.id', read_only=True, allow_null=True)

    is_paid = serializers.SerializerMethodField()
    can_accept = serializers.SerializerMethodField()

    class Meta:
        model = ConsultationRequest
        fields = [
            'id',
            'client_id',
            'client_name',
            'client_phone',
            'client_avatar',
            'date',
            'time',
            'status',
            'is_paid',
            'can_accept',
            'chat_room_id',
            'created_at',
            'paid_at',
            'accepted_at',
            'started_at',
            'completed_at',
        ]

    def get_is_paid(self, obj):
        return obj.status in ['paid', 'accepted', 'in_progress', 'completed']

    def get_client_name(self, obj):
        """
        Client nomi

        Priority:
        1. full_name field
        2. first_name + last_name
        3. Telefon (formatted)
        4. "Mijoz"
        """
        # 1. full_name field
        if hasattr(obj.client, 'full_name'):
            full_name = str(obj.client.full_name or '').strip()
            if full_name:
                return full_name

        # 2. first_name + last_name
        if hasattr(obj.client, 'first_name') and hasattr(obj.client, 'last_name'):
            first_name = str(obj.client.first_name or '').strip()
            last_name = str(obj.client.last_name or '').strip()

            if first_name and last_name:
                return f"{first_name} {last_name}"

            if first_name:
                return first_name

        # 3. Telefon (formatted)
        phone = str(obj.client.phone or '').strip()
        if phone:
            # 998949355757 → +998 94 935 57 57
            if phone.startswith('998') and len(phone) == 12:
                return f"+998 {phone[3:5]} {phone[5:8]} {phone[8:10]} {phone[10:]}"
            elif len(phone) >= 9:
                return f"+{phone}"
            return phone

        # 4. Default
        return "Mijoz"

    def get_client_avatar(self, obj):
        if hasattr(obj.client, 'avatar') and obj.client.avatar:
            avatar_url = obj.client.avatar.url

            # Request dan avtomatik domain
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(avatar_url)

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

    def get_can_accept(self, obj):
        return obj.status == 'paid'


class ConsultationListSerializer(serializers.ModelSerializer):
    """
    Qisqa ma'lumot (list uchun)
    """

    client_name = serializers.SerializerMethodField()
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    class Meta:
        model = ConsultationRequest
        fields = [
            'id',
            'client_name',
            'client_phone',
            'date',
            'time',
            'status',
            'created_at',
        ]

    def get_client_name(self, obj):
        """Client nomi"""
        # full_name
        if hasattr(obj.client, 'full_name'):
            full_name = str(obj.client.full_name or '').strip()
            if full_name:
                return full_name

        # first_name + last_name
        if hasattr(obj.client, 'first_name') and hasattr(obj.client, 'last_name'):
            first_name = str(obj.client.first_name or '').strip()
            last_name = str(obj.client.last_name or '').strip()

            if first_name and last_name:
                return f"{first_name} {last_name}"
            if first_name:
                return first_name

        # Telefon
        phone = str(obj.client.phone or '').strip()
        if phone:
            if phone.startswith('998') and len(phone) == 12:
                return f"+998 {phone[3:5]} {phone[5:8]} {phone[8:10]} {phone[10:]}"
            elif len(phone) >= 9:
                return f"+{phone}"
            return phone

        return "Mijoz"

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









