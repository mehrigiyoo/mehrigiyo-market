import json
from django.db.models import Sum
from rest_framework import serializers

from account.models import UserModel
from .models import Doctor, TypeDoctor, RateDoctor, Advertising, AdviceTime
from comment.models import CommentDoctor


class AdvertisingSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField(method_name='get_user_id')

    def get_user_id(self, instance):
        doctor_instance = instance.doctor
        try:
            user_model = UserModel.objects.get(specialist_doctor=doctor_instance, is_staff=True)
        except:
            return -1

        return user_model.id

    class Meta:
        model = Advertising
        fields = ['id', 'user_id', 'image', 'title', 'text']

class DoctorUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email', 'avatar', 'first_name', 'last_name']

class TypeDoctorSerializer(serializers.ModelSerializer):
    # get_doctors_count = serializers.SerializerMethodField('')
    class Meta:
        model = TypeDoctor
        fields = ['id', 'name', 'name_uz', 'name_ru', 'name_en', 'image', 'get_doctors_count']

class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField()
    type_doctor = TypeDoctorSerializer()
    rate = serializers.CharField(read_only=True, )
    is_favorite = serializers.BooleanField(read_only=True, )
    top = serializers.BooleanField(read_only=True, )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            usermodel = UserModel.objects.get(specialist_doctor=instance)
            representation['user'] = DoctorUserSerializer(usermodel).data
        except Exception as error:
            print(error)
            pass

        try:
            user = self.context['user']
            if instance in user.favorite_medicine.all():
                representation['is_favorite'] = True
            else:
                representation['is_favorite'] = False
        except:
            pass
        # doctors = CommentDoctor.objects.filter(doctor=representation,)
        # representation['rate'] = sum(instance.comments_doc.values('rate', flat=True))
        try:
            representation['rate'] = instance.total_rate or 0

            if representation['rate'] >= 4.5 and representation['review'] >= 15:
                representation['top'] = True
            else:
                representation['top'] = False
        except:
            pass
        # representation['rate'] = Sum(instance__comments_doc__rate)
        return representation

    class Meta:
        model = Doctor
        fields = '__all__'
        extra_fields = ['user', 'rate', 'is_favorite']


class RateSerializer(serializers.ModelSerializer):

    class Meta:
        model = RateDoctor
        fields = '__all__'

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.client = self.context['request'].user
        instance.save()
        return instance


class AdvicecDocSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    id = serializers.IntegerField()


class AdviceSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer()

    class Meta:
        model = AdviceTime
        fields = '__all__'



# Doctor gender analize serializers

class GenderStatisticsSerializer(serializers.Serializer):
    total_doctors = serializers.IntegerField()
    male_percentage = serializers.FloatField()
    female_percentage = serializers.FloatField()
    male_count = serializers.IntegerField()
    female_count = serializers.IntegerField()

