from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (DoctorsView, DoctorRetrieveView, TypeDoctorView, GetDoctorsWithType, GetSingleDoctor, AdviceView,
                    AdvertisingView, GenderStatisticsView)
router = DefaultRouter()
router.register(r'types', TypeDoctorView)
# router.register(r'types/one', GetDoctorsWithType)
urlpatterns = [
    # path('', include(router.urls)),
    # path('types/', TypeDoctorView.as_view({'list': 'get'})),
    # path('types/one/', GetDoctorsWithType.as_view()),
    path('types/', TypeDoctorView.as_view()),
    path('doctors/', DoctorsView.as_view()),
    path('doctors/<int:pk>/', DoctorRetrieveView.as_view()),
    path('advertising/', AdvertisingView.as_view()),
    path('doctors/one/', GetSingleDoctor.as_view({'list': 'get'})),
    path('advice/', AdviceView.as_view()),
    path('doctor/gender/', GenderStatisticsView.as_view()),
]
