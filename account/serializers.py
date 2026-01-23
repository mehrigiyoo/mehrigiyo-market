from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserModel, CountyModel, RegionModel, DeliveryAddress, OfferModel
from config.validators import PhoneValidator, normalize_phone


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


# class RegistrationSerializer(serializers.ModelSerializer):
#     invited = serializers.CharField(required=False, write_only=True)
#     password2 = serializers.CharField(write_only=True)  # password confirm
#
#     class Meta:
#         model = UserModel
#         fields = [
#             'phone', 'first_name', 'last_name',
#             'password', 'password2', 'email', 'avatar', 'role', 'invited'
#         ]
#         extra_kwargs = {
#             'password': {'write_only': True},
#             'avatar': {'required': False},
#             'email': {'required': False},
#             'role': {'required': False}
#         }
#
#     def validate(self, attrs):
#         if attrs.get('password') != attrs.get('password2'):
#             raise serializers.ValidationError({"password": "Passwordlar mos kelmayapti!"})
#
#         attrs['role'] = UserModel.Roles.CLIENT
#         return attrs
#
#     def create(self, validated_data):
#         inviter_code = validated_data.pop('invited', None)
#         validated_data.pop('password2', None)  # password2 faqat tekshiruv uchun
#
#         password = validated_data.pop('password', None)
#         user = UserModel.objects.create_user(password=password, **validated_data)
#         user.role = UserModel.Roles.CLIENT
#         user.save()
#
#         # ClientProfile yaratish
#         from client.models import ClientProfile
#         ClientProfile.objects.create(user=user)
#
#         # Referral va Payme jarayoni
#         if inviter_code:
#             inviter_qs = UserModel.objects.filter(phone=inviter_code).first()
#             if inviter_qs:
#                 try:
#                     Referrals.objects.create(
#                         user=inviter_qs,
#                         invited_user=user.phone
#                     )
#                     PaymeTransactionModel.objects.create(
#                         request_id=inviter_code,
#                         order_id=user.phone,
#                         phone=user.phone,
#                         amount=10000 * 100,
#                         status='processing',
#                         _type='referal',
#                     )
#                 except Exception:
#                     user.delete()
#                     raise serializers.ValidationError("Referral jarayoni muvaffaqiyatsiz bo‘ldi.")
#
#         return user

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
        fields = ['id', 'phone', 'first_name', 'last_name', 'referral_count', 'is_active']