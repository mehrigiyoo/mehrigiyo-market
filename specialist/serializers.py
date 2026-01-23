from django.db import IntegrityError
from rest_framework import serializers

from account.models import UserModel
from config.validators import normalize_phone
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
            'type_doctor', 'average_rating', 'rating_count',
            'stars', 'top'
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
            'id', 'full_name', 'image', 'experience', 'description',
            'type_doctor', 'average_rating', 'rating_count',
            'stars', 'view_count', 'top', 'birthday', 'gender'
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
