from rest_framework import serializers

from comment.models import CommentDoctor, CommentMedicine, QuestionModel


class CommentDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentDoctor
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False},
            'doctor': {'required': False},
        }


class CommentMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentMedicine
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False},
            'medicine': {'required': False},
        }


class CommentPostSerializer(serializers.Serializer):
    pk = serializers.IntegerField(required=True)
    text = serializers.CharField(max_length=500, required=False)
    rate = serializers.IntegerField(max_value=5, required=False, default=1)


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionModel
        fields = '__all__'
