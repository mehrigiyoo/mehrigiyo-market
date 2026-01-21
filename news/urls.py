from django.urls import path
from .views import NewsView, NewsRetrieveView, TagView, AdvertisingShopView, \
    NotificationView, LinksListApiView, StoriesDetailView, StoriesListView

urlpatterns = [
    path('', NewsView.as_view()),
    path('<int:pk>/', NewsRetrieveView.as_view()),
    path('tags/', TagView.as_view()),
    path('advertising/', AdvertisingShopView.as_view()),
    path('notification/', NotificationView.as_view()),
    # path('notification/call/', NotificationCallView.as_view()),

    path('stories/', StoriesListView.as_view(), name='stories-list'),
    path('stories/<int:pk>/', StoriesDetailView.as_view(), name='stories-detail'),

    path('links/', LinksListApiView.as_view()),
]
