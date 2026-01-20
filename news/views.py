from django.db.models import QuerySet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from shop.models import Feedbacks
from .filters import NewsFilter
from .models import NewsModel, Stories, TagsModel, Advertising, Notification
from .serializers import (
    FeedbackLinksSerializer,
    NewsModelSerializer,
    StoriesSerializer,
    TagsSerializer,
    AdvertisingSerializer,
    NotificationSerializer,
)


class NewsView(generics.ListAPIView):
    queryset = NewsModel.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = NewsModelSerializer
    filterset_class = NewsFilter

    @swagger_auto_schema(
        operation_id="news-list",
        operation_description="getting list of news",
        responses={"200": NewsModelSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                "tag_id",
                openapi.IN_QUERY,
                description="test manual params",
                type=openapi.TYPE_STRING,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        key = request.GET.get("tag_id", False)
        if key:
            keys = key.split(",")
            self.queryset = NewsModel.objects.filter(hashtag_id__id__in=keys)
        return self.list(request, *args, **kwargs)


class NewsRetrieveView(generics.RetrieveAPIView):
    queryset = NewsModel.objects.all()
    serializer_class = NewsModelSerializer

    @swagger_auto_schema(
        operation_id="news-detail",
        operation_description="retrieving the news",
        responses={"200": NewsModelSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class TagView(APIView):
    queryset = TagsModel.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = TagsSerializer

    @swagger_auto_schema(
        operation_id="tags",
        operation_description="get tags",
        # request_body=TagsSerializer(),
        responses={"200": TagsSerializer()},
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Number of results to return per page.",
                type=openapi.TYPE_NUMBER,
            )
        ],
    )
    def get(self, request):
        key = request.GET.get("limit", False)
        asd = TagsModel.objects.all()
        if key:
            asd = TagsModel.objects.all()[: int(key)]
        serializer = TagsSerializer(asd, many=True)
        return Response(data=serializer.data)

    # def get(self, request, *args, **kwargs):

    # return self.list(request, *args, **kwargs)

    # @swagger_auto_schema(
    #     operation_id='tags',
    #     operation_description="post tags",
    #     request_body=InputSerializer(),
    #     responses={
    #         '200': TagsWithNewsSerializer()
    #     },
    # )
    # def post(self, request, *args, **kwargs):
    #     self.queryset = TagsModel.objects.filter(tag_name=request.data['tag'])
    #     return self.list(request, *args, **kwargs)


class StoriesView(generics.ListAPIView):
    queryset = Stories.objects.all()
    serializer_class = StoriesSerializer

    def filter_queryset(self, queryset: QuerySet[Stories]):
        return queryset.exclude(contents=None).order_by("id")

    @swagger_auto_schema(
        operation_id="stories-list",
        operation_description="list stories",
        responses={"200": StoriesSerializer()},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)

            for stories in serializer.data:
                contents = stories["contents"]
                contents.sort(key=lambda x: x["id"])

            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # def get(self, request, *args, **kwargs):
    #     return self.list(request, *args, **kwargs)


class StoriesRetrieveView(generics.RetrieveAPIView):
    queryset = Stories.objects.all()
    serializer_class = StoriesSerializer

    @swagger_auto_schema(
        operation_id="stories-retrieve",
        operation_description="retrieving the stories",
        responses={"200": StoriesSerializer()},
    )
    def get(self, request, *args, **kwargs):
        # stories = self.retrieve(request, *args, **kwargs)
        # stories.contents.sort(lambda x: x['id'])

        instance = self.get_object()
        stories = self.get_serializer(instance)

        contents = stories.data["contents"]
        contents.sort(key=lambda x: x["id"])

        return Response(stories.data)


class AdvertisingShopView(generics.ListAPIView):
    queryset = Advertising.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = AdvertisingSerializer

    # pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(
        operation_id="advertising",
        operation_description="advertisingView",
        # request_body=AdvertisingSerializer(),
        responses={"200": AdvertisingSerializer()},
    )
    def post(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class NotificationView(generics.ListAPIView):
    queryset = Notification.objects.all().order_by("-id")
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id="notification",
        operation_description="get notifications",
        # request_body=NotificationSerializer(),
        responses={"200": NotificationSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class LinksListApiView(generics.ListAPIView):
    queryset = Feedbacks.objects.filter(medicine=None, type="feedback_client")
    serializer_class = FeedbackLinksSerializer
    filter_backends = (
        OrderingFilter,
        SearchFilter,
    )

    ordering = ("id",)
    search_fields = ("category",)
