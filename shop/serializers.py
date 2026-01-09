import json
from rest_framework import serializers
from .models import Feedbacks, PicturesMedicine, TypeMedicine, Medicine, CartModel, OrderModel
from account.serializers import DeliverAddressSerializer
from account.models import DeliveryAddress, UserModel


class PicturesMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PicturesMedicine
        fields = '__all__'


class TypeMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeMedicine
        fields = '__all__'


class MedicineSerializer(serializers.ModelSerializer):
    pictures = PicturesMedicineSerializer(many=True)
    is_favorite = serializers.SerializerMethodField(method_name="get_favorites")
    feedbacks = serializers.SerializerMethodField(method_name="get_feedbacks")
    instructions = serializers.SerializerMethodField(method_name="get_instructions")

    def get_instructions(self, medicine: Medicine):
        result = []

        try:
            feedbacks = Feedbacks.objects.filter(medicine=medicine, type="product_instruction")

            for feedback in feedbacks:
                video_id = feedback.link.split("/").pop()
                result.append({
                    "link": feedback.link,
                    "image": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                })

            return result
        except:
            return result

    def get_feedbacks(self, medicine: Medicine):
        result = []

        try:
            feedbacks = Feedbacks.objects.filter(medicine=medicine, type="feedback_product")

            for feedback in feedbacks:
                video_id = feedback.link.split("/").pop()
                result.append({
                    "link": feedback.link,
                    "image": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                })

            return result
        except:
            return result

    def get_feedback_client(self, medicine: Medicine):
        result = []

        try:
            feedbacks = Feedbacks.objects.filter(medicine=medicine, type="feedback_client")

            for feedback in feedbacks:
                video_id = feedback.link.split("/").pop()
                result.append({
                    "link": feedback.link,
                    "image": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                })

            return result
        except:
            return result

    def get_favorites(self, medicine: Medicine):
        try:
            user: UserModel = self.context['user']

            if medicine in user.favorite_medicine.all():
                return True

        except:
            print("error")

        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # try:
        #     user = self.context['user']
        #     if instance in user.favorite_medicine.all():

        #         representation['is_favorite'] = True
        #     else:
        #         representation['is_favorite'] = False
        # except:
        #     pass
        try:
            representation['rate'] = instance.total_rate or 0
        except:
            pass
        return representation

    class Meta:
        model = Medicine
        fields = "__all__"


class CartSerializer(serializers.ModelSerializer):
    product = MedicineSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CartModel
        fields = ('id', 'user', 'amount', 'product', 'get_total_price')
        extra_kwargs = {
            'user': {'required': False},
            'amount': {'required': False},
            'product': {'required': False}
        }

    def create(self, validated_data):
        request = self.context.get('request', None)
        instance = self.Meta.model(**validated_data)
        instance.user = request.user
        # instance.product = request.data['product']
        instance.save()
        return instance


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
