from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin
from paymeuz.models import PaymeTransactionModel, Card


class OwnerFilter(AutocompleteFilter):
    title = "Owner"
    field_name = 'owner'


class PaymeTransactionAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('id', '_id', 'request_id', 'phone', 'amount', 'order_id', 'state', 'status', 'date', 'create_time', 'perform_time', 'cancel_time', 'cancel_reason', )
    list_display_links = ('id',)
    list_filter = ('state', 'status', 'cancel_reason', )
    search_fields = ('id', '_id', 'request_id', 'phone', 'amount', )


class CardAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'number', 'expire', 'token', 'recurrent', 'verify', 'is_deleted', ]
    list_filter = [OwnerFilter, 'recurrent', 'verify', 'is_deleted', ]
    search_fields = ['id', 'number', 'expire', 'token', ]
    autocomplete_fields = ['owner', ]


admin.site.register(PaymeTransactionModel, PaymeTransactionAdmin)
admin.site.register(Card, CardAdmin)
