from rest_framework import serializers
from .models import UserModel, CountyModel, RegionModel, DeliveryAddress, OfferModel
from config.validators import PhoneValidator


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferModel
        fields = '__all__'


class PkSerializer(serializers.Serializer):
    pk = serializers.IntegerField(required=True)


class RegionPostSerializer(serializers.Serializer):
    region = serializers.IntegerField(required=True)


class RegionPutSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    region = serializers.IntegerField(required=True)


class CheckPhoneNumberSerializer(serializers.Serializer):
    phone = serializers.CharField()


class SmsSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PhoneValidator()])
    signature = serializers.CharField(required=False, default="")


class ConfirmSmsSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PhoneValidator()])
    code = serializers.CharField(min_length=6, max_length=6)


class ChangePasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=50, min_length=6)
    new_password = serializers.CharField(max_length=50, min_length=6)


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['username', 'first_name', 'last_name', 'password', 'email', 'avatar']
        extra_kwargs = {
            'password': {'write_only': True},
            'avatar': {'required': False},
            'email': {'required': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CountyModel
        fields = ('id', 'name', 'name_uz', 'name_ru', 'name_en')


class RegionSerializer(serializers.ModelSerializer):
    # country = CountrySerializer()
    id = serializers.ReadOnlyField()

    class Meta:
        model = RegionModel
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    address = RegionSerializer(read_only=True)

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'avatar', 'address', 'language',
                  'favorite_medicine', 'favorite_doctor', 'theme_mode', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'username': {'read_only': True},
            'favorite_medicine': {'read_only': True},
            'favorite_doctor': {'read_only': True},
            'address': {'read_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
            'avatar': {'required': False},
            'language': {'required': False},
            'theme_mode': {'required': False},
        }


class DeliverAddressSerializer(serializers.ModelSerializer):
    region = RegionSerializer(required=False)

    class Meta:
        model = DeliveryAddress
        fields = ['id', 'name', 'region', 'full_address', 'apartment_office', 'floor', 'door_or_phone', 'instructions']
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {'required': False},
            'region': {'required': False},
            'full_address': {'required': False},
            'apartment_office': {'required': False},
            'floor': {'required': False},
            'door_or_phone': {'required': False},
            'instructions': {'required': False},
        }



class ReferalUserSerializer(serializers.ModelSerializer):
    referral_count = serializers.IntegerField(source='referrals.count', read_only=True)

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'first_name', 'last_name', 'referral_count', 'is_active']