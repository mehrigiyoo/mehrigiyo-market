from .models import Doctor
import django_filters


class DoctorFilter(django_filters.FilterSet):

    class Meta:
        model = Doctor
        fields = ['id', 'full_name', 'experience', 'description']
