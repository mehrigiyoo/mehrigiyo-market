from django.db.models import QuerySet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from account.models import UserModel
from news.tasks import send_notification_func
from shop.models import Feedbacks
from .filters import NewsFilter
from .models import NewsModel, Stories, TagsModel, Advertising, Notification
from .send_notification import sendPush
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

        # else:
        #     for response in res.responses:
        #         if response.exception:
        #             response_index = res.responses.index(response)
        #             if response_index == 0:
        #                 error_device = 'Android'
        #             else:
        #                 error_device = 'IOS'

        #             return Response(data={'message': f'failed for {error_device}. Exception: {response.exception}'})


class NotificationCallView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id="call_notification",
        operation_description="Post Call notifications",
        responses={
            "200": openapi.Response("Successful Operation", NotificationSerializer())
        },
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_QUERY,
                description="Send User Id",
                type=openapi.TYPE_NUMBER,
            )
        ],
    )
    def post(self, request):
        # pk = request.GET.get("pk", False)

        user_id = request.data.get("user_id", None)
        title = request.data.get("title", None)
        description = request.data.get("description", None)
        type = request.data.get("type", None)
        image = request.data.get("image", None)

        # current_user = request.user
        push_time = timezone.now()
        registration_tokens = []

        if user_id == "0":
            keys = list(
                UserModel.objects.filter().values_list("notificationKey", flat=True)
            )
            for key in keys:
                registration_tokens.append(key or "-1")
        else:
            user = UserModel.objects.get(id=user_id)
            registration_tokens.append(user.notificationKey or "-1")

        # Create and save Notification object
        notification = Notification(
            title=title,
            description=description,
            type=type,
            image=image,
            push_time=push_time,
            foreign_id=user_id,
        )
        notification.save()

        # Sending to Firebase
        # image_path = None
        # try:
        #     image_path = current_user.avatar.path
        # except:
        #     pass

        # res = sendPush(
        #     title=title,
        #     description=description,
        #     registration_tokens=registration_tokens,
        #     image=image_path,
        # )
        # success_count = res.success_count

        image_path = None
        try:
            image_path = notification.image.path
        except:
            pass

        send_notification_func.s(
            title=title,
            description=description,
            image_path=image_path,
            type=type,
            foreign_id=user_id,
        ).apply_async(countdown=5)

        # if success_count == 0:
        #     return Response(
        #         data={"message": f"Failed. Exceptions: {res.responses[0].exception}"}
        #     )

        return Response(data={"message": "Success!"})


# class NotificationCallView(APIView):
#     permission_classes = (IsAuthenticated,)
#
#     @swagger_auto_schema(
#         operation_id='call_notification',
#         operation_description="post Call notifications",
#         # request_body=NotificationSerializer(),
#         responses={
#             '200': NotificationSerializer()
#         },
#         manual_parameters=[
#             openapi.Parameter('pk', openapi.IN_QUERY, description="Send USer Id",
#                               type=openapi.TYPE_NUMBER)
#         ],
#     )
#     def post(self, request):
#         pk = request.GET.get('pk', False)
#         user = UserModel.objects.get(id=pk)
#         current_user = request.user
#
#
#         # sending to firebase
#         image_path = None
#         try:
#             current_user.avatar.path
#         except:
#             pass
#
#         res = sendPush(title='CALL', description=current_user.get_full_name(),
#                        registration_tokens=[user.notificationKey],
#                        image=image_path)
#         success_count = res.success_count
#
#         if success_count == 0:
#             return Response(data={'message': f'failed. Exceptions:'
#                                              f'{res.responses[0].exception}'})
#             # notification.save()
#         return Response(data={'message': f'success!'})

# if success_count == 2:
#     return Response({'message': f'success!'})
# elif success_count == 0:
#     return Response({'message': f'failed for both Android and IOS. Exceptions: Android: '
#                                 f'{res.responses[0].exception}, IOS: {res.responses[1].exception}]'})
# else:
#     for response in res.responses:
#         if response.exception:
#             response_index = res.responses.index(response)
#             if response_index == 0:
#                 error_device = 'Android'
#             else:
#                 error_device = 'IOS'

#             return Response({'message': f'failed for {error_device}. Exception: {response.exception}'})


class LinksListApiView(generics.ListAPIView):
    queryset = Feedbacks.objects.filter(medicine=None, type="feedback_client")
    serializer_class = FeedbackLinksSerializer
    filter_backends = (
        OrderingFilter,
        SearchFilter,
    )

    ordering = ("id",)
    search_fields = ("category",)
