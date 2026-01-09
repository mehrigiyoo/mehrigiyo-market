from django.urls import path
from .views import CommentDoctorView, CommentMedicineView, QuestionView

urlpatterns = [
    path('doctor/', CommentDoctorView.as_view()),
    path('medicine/', CommentMedicineView.as_view()),
    path('question/', QuestionView.as_view()),
]
