from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer, CharField, SerializerMethodField

from account.models import UserModel
from shop.models import Feedbacks
from .models import NewsModel, Stories, TagsModel, Advertising, Notification, StoriesImage


class StoriesImageSerializer(ModelSerializer):
    class Meta:
        model = StoriesImage
        fields = ['id', 'image']

class StoriesSerializer(serializers.ModelSerializer):
    images = StoriesImageSerializer(many=True, read_only=True)

    class Meta:
        model = Stories
        fields = [
            'id', 'title', 'title_uz', 'title_ru', 'title_en',
            'icon', 'images'
        ]


class AdvertisingSerializer(ModelSerializer):
    user_id = SerializerMethodField(method_name='get_user_id')

    def get_user_id(self, instance):
        doctor_instance = instance.doctor
        try:
            user_model = UserModel.objects.get(specialist_doctor=doctor_instance, is_staff=True)
        except:
            return -1

        return user_model.id

    class Meta:
        model = Advertising
        fields = '__all__'
        ref_name = "Shop_ad"


class TagsSerializer(ModelSerializer):
    class Meta:
        model = TagsModel
        fields = '__all__'


class NewsModelSerializer(ModelSerializer):
    hashtag = TagsSerializer()

    class Meta:
        model = NewsModel
        fields = '__all__'


class TagsWithNewsSerializer(ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        n = NewsModel.objects.filter(hashtag__tag_name=representation['tag_name'])
        representation['news'] = NewsModelSerializer(n, many=True).data
        return representation

    class Meta:
        model = TagsModel
        fields = ['tag_name']


class InputSerializer(Serializer):
    tag = CharField(max_length=50)


class FeedbackLinksSerializer(ModelSerializer):
    image = SerializerMethodField(method_name="get_image")

    def get_image(self, instance: Feedbacks):
        video_id = instance.link.split("/").pop()
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    class Meta:
        model = Feedbacks
        fields = ('id', 'link', 'image')


class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        # extra_kwargs = {
        #     'title': {'required': True},
        #     'description': {'required': True},
        # }
