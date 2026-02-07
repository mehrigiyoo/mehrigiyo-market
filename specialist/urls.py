from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (TypeDoctorListAPI,
                    AdvertisingView, GenderStatisticsView, AvailableSlotsView, BookAdviceView, WorkScheduleViewSet,
                    DoctorUnavailableViewSet, DoctorProfileView, DoctorRegisterView, DoctorListAPI, DoctorDetailAPI,
                    DoctorRatingCreateAPI)
router = DefaultRouter()
# router.register(r'types', TypeDoctorListAPI)
router.register(r'work-schedules', WorkScheduleViewSet, basename='work-schedules')
router.register(r'doctor-unavailable', DoctorUnavailableViewSet, basename='doctor-unavailable')


# router.register(r'types/one', GetDoctorsWithType)
urlpatterns = [
    # path('', include(router.urls)),
    path('doctor/register/', DoctorRegisterView.as_view(), name='doctor-registerr'),
    path('doctor/profile/', DoctorProfileView.as_view()),


    path('types/', TypeDoctorListAPI.as_view(), name='type-doctor-list'),
    path('doctors/', DoctorListAPI.as_view(), name='doctor-list'),
    path('doctor/<int:id>/', DoctorDetailAPI.as_view(), name='doctor-detail'),
    path('doctor/rate/', DoctorRatingCreateAPI.as_view(), name='doctor-rate'),
    path('advertising/', AdvertisingView.as_view()),
    # path('advice/', AdviceView.as_view()),
    path('doctor/gender/', GenderStatisticsView.as_view()),
    path('available-slots/', AvailableSlotsView.as_view(), name='available-slots'),
    path('book-advice/', BookAdviceView.as_view(), name='book-advice'),

]
