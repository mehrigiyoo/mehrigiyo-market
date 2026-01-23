import json

from django.db.models import Avg
from rest_framework import serializers
from .models import Feedbacks, PicturesMedicine, TypeMedicine, Medicine, CartModel, OrderModel
from account.serializers import DeliverAddressSerializer
from account.models import DeliveryAddress, UserModel


class PicturesMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PicturesMedicine
        fields = ['id', 'image']


class TypeMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeMedicine
        fields = '__all__'


class MedicineSerializer(serializers.ModelSerializer):
    pictures = PicturesMedicineSerializer(many=True, read_only=True)
    rate = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    feedbacks = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()

    def get_rate(self, obj):
        return obj.comments_med.aggregate(rate_avg=Avg('rate'))['rate_avg'] or 0

    def get_is_favorite(self, obj):
        user = self.context.get('user')
        if not user or user.is_anonymous:
            return False
        return user.favorite_medicine.filter(id=obj.id).exists()

    def _get_feedback(self, medicine, feedback_type):
        return [
            {
                "link": f.link,
                "image": f"https://img.youtube.com/vi/{f.link.split('/').pop()}/hqdefault.jpg"
            }
            for f in Feedbacks.objects.filter(
                medicine=medicine,
                type=feedback_type
            )
        ]

    def get_feedbacks(self, obj):
        return self._get_feedback(obj, "feedback_product")

    def get_instructions(self, obj):
        return self._get_feedback(obj, "product_instruction")

    class Meta:
        model = Medicine
        fields = [
            'id', 'image', 'name', 'title', 'order_count', 'description',
            'quantity', 'review', 'weight', 'type_medicine', 'cost', 'discount',
            'created_at', 'product_inn', 'product_ikpu', 'product_package_code',
            'content_uz', 'content_ru', 'content_en',
            'features_uz', 'features_ru', 'features_en',
            'certificates_uz', 'certificates_ru', 'certificates_en',
            'application_uz', 'application_ru', 'application_en',
            'contraindications_uz', 'contraindications_ru', 'contraindications_en',
            'rate', 'is_favorite', 'feedbacks', 'instructions', 'pictures'
        ]

class CartSerializer(serializers.ModelSerializer):
    product = MedicineSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    class Meta:
        model = CartModel
        fields = ('id', 'product', 'amount', 'total_price')

    def get_total_price(self, obj):
        return obj.total_price  # propertyni shunchaki chaqiramiz, () kerak emas


class CartCreateUpdateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False)
    amount = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not Medicine.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Product not found")
        return value


class CartPostSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    amount = serializers.IntegerField()


class PutSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class CartPutSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()


class OrderPutSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    shipping_address = serializers.IntegerField()
    credit_card = serializers.IntegerField()


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderModel
        fields = ('id', 'user', 'credit_card', 'shipping_address', 'cart_products', 'price', 'payment_type',
                  'payment_status', 'delivery_status', 'created_at')
        extra_kwargs = {
            'cart_products': {'required': False}
        }


class OrderShowSerializer(serializers.ModelSerializer):
    shipping_address = DeliverAddressSerializer()
    cart_products = CartSerializer(many=True)

    class Meta:
        model = OrderModel
        fields = '__all__'
        extra_kwargs = {
            'delivery': {'required': False}
        }

    def update(self, instance, validated_data):
        try:
            id = validated_data['shipping_address']
            da = DeliveryAddress.objects.get(id=id)
            instance.shipping_address = da
            instance.price = instance.price + da.region.delivery_price
            instance.save()

        except:
            pass
        print(instance)
        print(validated_data)
        instance.save()


class ListSerializer(serializers.Serializer):
    list = serializers.CharField()




class OrderStatusSerializer(serializers.Serializer):
    delivered_count = serializers.IntegerField()
    delivered_percentage = serializers.FloatField()
    in_progress_count = serializers.IntegerField()
    in_progress_percentage = serializers.FloatField()
    canceled_count = serializers.IntegerField()
    canceled_percentage = serializers.FloatField()
    total_orders = serializers.IntegerField()
    doctor_count = serializers.IntegerField()
    product_total = serializers.IntegerField()
    client_count = serializers.IntegerField()
    delivered_count_all = serializers.IntegerField()





class MedicineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'
