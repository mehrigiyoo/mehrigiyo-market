from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (TypeDoctorView, GetSingleDoctor,
                    AdvertisingView, GenderStatisticsView, AvailableSlotsView, BookAdviceView, WorkScheduleViewSet,
                    DoctorUnavailableViewSet, DoctorProfileView, DoctorRegisterView)
router = DefaultRouter()
router.register(r'types', TypeDoctorView)
router.register(r'work-schedules', WorkScheduleViewSet, basename='work-schedules')
router.register(r'doctor-unavailable', DoctorUnavailableViewSet, basename='doctor-unavailable')


# router.register(r'types/one', GetDoctorsWithType)
urlpatterns = [
    # path('', include(router.urls)),
    # path('types/', TypeDoctorView.as_view({'list': 'get'})),
    # path('types/one/', GetDoctorsWithType.as_view()),
    path('doctor/register/', DoctorRegisterView.as_view(), name='doctor-register'),
    path('doctor/profile/', DoctorProfileView.as_view()),


    path('types/', TypeDoctorView.as_view()),
    # path('doctors/', DoctorsView.as_view()),
    # path('doctors/<int:pk>/', DoctorRetrieveView.as_view()),
    path('advertising/', AdvertisingView.as_view()),
    path('doctors/one/', GetSingleDoctor.as_view({'list': 'get'})),
    # path('advice/', AdviceView.as_view()),
    path('doctor/gender/', GenderStatisticsView.as_view()),
    path('available-slots/', AvailableSlotsView.as_view(), name='available-slots'),
    path('book-advice/', BookAdviceView.as_view(), name='book-advice'),

]
