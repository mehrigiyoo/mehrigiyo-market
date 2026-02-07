from django.urls import path, include
from rest_framework.routers import DefaultRouter

from client.views import ClientConsultationViewSet
from specialist.views import DoctorConsultationViewSet
from .views import ConsultationViewSet

router = DefaultRouter()

# Umumiy (create uchun)
router.register(r'consultations', ConsultationViewSet, basename='consultation')

# Doctor uchun
router.register(r'doctor/consultations', DoctorConsultationViewSet, basename='doctor-consultation')

# Client uchun
router.register(r'client/consultations', ClientConsultationViewSet, basename='client-consultation')

urlpatterns = [
    path('', include(router.urls)),
]

"""
=== Client Endpoints ===
- GET    /api/consultations/availability/               - Doctor mavjudligi
- POST   /api/consultations/create_consultation/        - Yangi konsultatsiya (DOIM success)

- GET    /api/client/consultations/                     - Barcha konsultatsiyalar
- GET    /api/client/consultations/active/              - Faol (paid, accepted, in_progress)
- GET    /api/client/consultations/history/             - Tarix (completed, cancelled)
- GET    /api/client/consultations/{id}/                - Detail
- POST   /api/client/consultations/{id}/cancel/         - Bekor qilish

=== Doctor Endpoints ===
- GET    /api/doctor/consultations/                     - Barcha konsultatsiyalar
- GET    /api/doctor/consultations/new/                 - Yangi (paid)
- GET    /api/doctor/consultations/active/              - Active (accepted, in_progress)
- GET    /api/doctor/consultations/completed/           - Tugatilganlar
- GET    /api/doctor/consultations/{id}/                - Detail
- POST   /api/doctor/consultations/{id}/accept/         - Qabul qilish
- POST   /api/doctor/consultations/{id}/complete/       - Tugatish
"""