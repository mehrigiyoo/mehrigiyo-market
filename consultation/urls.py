from django.urls import path, include
from rest_framework.routers import DefaultRouter
from consultation.views import ConsultationViewSet
from specialist.views import DoctorConsultationViewSet

router = DefaultRouter()
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'doctor/consultations', DoctorConsultationViewSet, basename='doctor-consultation')


urlpatterns = [
    path('', include(router.urls)),
]


"""
Client endpoints:
- GET    /api/consultations/                      - Mening konsultatsiyalarim
- GET    /api/consultations/availability/          - Doctor mavjudligi
- POST   /api/consultations/create_consultation/   - Yangi konsultatsiya
- POST   /api/consultations/{id}/cancel/           - Bekor qilish

Doctor endpoints:
- GET    /api/doctor/consultations/                - Barcha konsultatsiyalar
- GET    /api/doctor/consultations/new/            - Yangi (paid)
- GET    /api/doctor/consultations/active/         - Active (accepted, in_progress)
- GET    /api/doctor/consultations/completed/      - Tugatilganlar
- GET    /api/doctor/consultations/{id}/           - Batafsil
- POST   /api/doctor/consultations/{id}/accept/    - Qabul qilish + room yaratish
"""














