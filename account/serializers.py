from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserModel, CountyModel, RegionModel, OfferModel, UserDevice
from config.validators import PhoneValidator, normalize_phone


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

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


class PhoneCheckSerializer(serializers.Serializer):
    phone = serializers.CharField(
        validators=[PhoneValidator()],
        max_length=20
    )

    def validate_phone(self, value):
        # Telefon raqamini normalize qilamiz
        return normalize_phone(value)


class SmsSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PhoneValidator()])
    purpose = serializers.ChoiceField(
        choices=['register', 'activate', 'reset_password']
    )


class ConfirmSmsSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PhoneValidator()])
    code = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.ChoiceField(
        choices=['register', 'activate', 'reset_password']
    )



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Parollar mos kelmadi")
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Parollar mos kelmadi")
        return attrs



class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('avatar',)


class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        return data


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
        fields = ['id', 'phone', 'first_name', 'last_name', 'email', 'avatar', 'address', 'language',
                  'favorite_medicine', 'theme_mode', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'phone': {'read_only': True},
            'favorite_medicine': {'read_only': True},
            'address': {'read_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
            'avatar': {'required': False},
            'language': {'required': False},
            'theme_mode': {'required': False},
        }


class UserDeviceSerializer(serializers.ModelSerializer):
    """Device serializer"""

    class Meta:
        model = UserDevice
        fields = [
            'id', 'fcm_token', 'device_id', 'device_type',
            'device_name', 'is_active', 'created_at', 'last_active'
        ]
        read_only_fields = ['id', 'created_at', 'last_active']

    def create(self, validated_data):
        """Create or update device"""
        user = self.context['request'].user
        device_id = validated_data.get('device_id')

        # Check if device exists
        device, created = UserDevice.objects.update_or_create(
            user=user,
            device_id=device_id,
            defaults=validated_data
        )

        return device


class ReferalUserSerializer(serializers.ModelSerializer):
    referral_count = serializers.IntegerField(source='referrals.count', read_only=True)

    class Meta:
        model = UserModel
        fields = ['id', 'phone', 'first_name', 'last_name', 'referral_count', 'is_active']


