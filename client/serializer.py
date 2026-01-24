# serializers.py
from rest_framework import serializers
from account.models import UserModel, Referrals
from client.models import ClientProfile, ClientAddress
from paymeuz.models import PaymeTransactionModel



class ClientProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)


    class Meta:
        model = ClientProfile
        fields = (
            'phone',
            'avatar',
            'full_name',
            'gender',
            'birthday',
        )


class ClientRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    full_name = serializers.CharField()
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')])
    age = serializers.IntegerField(min_value=1, max_value=120)

    invited = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Parollar mos emas")
        return attrs

    def create(self, validated_data):
        from client.models import ClientProfile
        from datetime import date

        age = validated_data.pop('age')
        birthday = date.today().replace(year=date.today().year - age)

        invited = validated_data.pop('invited', None)
        password = validated_data.pop('password')
        validated_data.pop('password2')

        user = UserModel.objects.create_user(
            phone=validated_data['phone'],
            password=password,
            role=UserModel.Roles.CLIENT,
            # is_active = True
        )

        ClientProfile.objects.create(
            user=user,
            full_name=validated_data['full_name'],
            gender=validated_data['gender'],
            birthday=birthday
        )

        if invited:
            inviter = UserModel.objects.filter(phone=invited).first()
            if inviter:
                Referrals.objects.create(user=inviter, invited_user=user.phone)
                PaymeTransactionModel.objects.create(
                    request_id=inviter.phone,
                    order_id=user.phone,
                    phone=user.phone,
                    amount=10000 * 100,
                    status='processing',
                    _type='referal'
                )

        return user



class ClientAvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField()


class ClientAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAddress
        fields = [
            'id', 'address_line', 'home', 'entrance', 'floor', 'apartment',
            'add_phone', 'comment', 'latitude', 'longitude', 'is_default',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
