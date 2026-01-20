from rest_framework import serializers
from .models import Operator

class OperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operator
        fields = (
            'full_name',
            'image',
            'birthday',
            'gender',
        )

class OperatorProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operator
        fields = (
            'full_name',
            'image',
            'birthday',
        )
