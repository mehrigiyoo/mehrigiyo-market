from django.contrib import admin
from .models import Operator

class OperatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'user', 'gender', 'created_at')
    search_fields = ('full_name', 'user__username')
    list_filter = ('gender',)
    autocomplete_fields = ['user']

admin.site.register(Operator, OperatorAdmin)
