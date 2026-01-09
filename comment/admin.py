from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin
from comment.models import CommentDoctor, CommentMedicine, QuestionModel


class DoctorFilter(AutocompleteFilter):
    title = "Doctor"
    field_name = 'doctor'


class UserFilter(AutocompleteFilter):
    title = "User"
    field_name = 'user'


class MedicineFilter(AutocompleteFilter):
    title = "Medicine"
    field_name = 'medicine'


class CommentDoctorAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'doctor', 'user', 'text', 'rate', 'created_at', ]
    list_filter = [DoctorFilter, UserFilter, 'rate', ]
    search_fields = ['id', 'text', ]
    autocomplete_fields = ['doctor', 'user', ]


class CommentMedicineAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'medicine', 'user', 'text', 'rate', 'created_at', ]
    list_filter = [MedicineFilter, UserFilter, 'rate', ]
    search_fields = ['id', 'text', ]
    autocomplete_fields = ['medicine', 'user', ]


class QuestionModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'phone', 'question', 'answer', ]
    list_filter = ['answer', ]
    search_fields = ['id', 'full_name', 'email', 'phone', 'question', 'answer', ]


admin.site.register(CommentDoctor, CommentDoctorAdmin)
admin.site.register(CommentMedicine, CommentMedicineAdmin)
admin.site.register(QuestionModel, QuestionModelAdmin)
