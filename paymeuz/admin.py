from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, PaymentTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_phone', 'payment_type', 'amount_display',
        'payment_method', 'status_badge', 'created_at'
    ]
    list_filter = ['payment_type', 'payment_method', 'status', 'created_at']
    search_fields = ['id', 'user__phone', 'payme_transaction_id']
    readonly_fields = [
        'id', 'user', 'content_type', 'object_id',
        'payme_transaction_id', 'ip_address', 'user_agent',
        'created_at', 'paid_at', 'cancelled_at'
    ]

    fieldsets = (
        ('Payment Info', {
            'fields': ('id', 'user', 'payment_type', 'amount', 'currency')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Payment Method', {
            'fields': ('payment_method', 'status')
        }),
        ('Payme Details', {
            'fields': ('payme_transaction_id', 'payme_time', 'payme_state')
        }),
        ('Security', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'paid_at', 'cancelled_at')
        }),
        ('Metadata', {
            'fields': ('description', 'metadata', 'gateway_response'),
            'classes': ('collapse',)
        }),
    )

    def user_phone(self, obj):
        return obj.user.phone

    user_phone.short_description = 'User'

    def amount_display(self, obj):
        return f"{obj.amount:,.0f} {obj.currency}"

    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'paid': 'green',
            'failed': 'red',
            'cancelled': 'orange',
            'refunded': 'purple',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.status.upper()
        )

    status_badge.short_description = 'Status'

    def has_add_permission(self, request):
        return False  # Cannot create payments via admin

    def has_delete_permission(self, request, obj=None):
        return False  # Cannot delete payments

    actions = ['export_to_excel']

    def export_to_excel(self, request, queryset):
        """Export selected payments to Excel"""
        # Implement Excel export if needed
        pass

    export_to_excel.short_description = "Export to Excel"


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'payment_id', 'transaction_id',
        'method', 'state', 'created_at'
    ]
    list_filter = ['method', 'state', 'created_at']
    search_fields = ['transaction_id', 'payment__id']
    readonly_fields = ['payment', 'transaction_id', 'method', 'created_at']

    fieldsets = (
        ('Transaction Info', {
            'fields': ('payment', 'transaction_id', 'method', 'state')
        }),
        ('Data', {
            'fields': ('request_data', 'response_data'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False