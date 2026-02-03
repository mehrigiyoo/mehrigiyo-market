from django.contrib import admin
from django.utils.html import format_html
from .models import Partner, PartnerRequest


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'api_key', 'is_active',
        'total_requests', 'total_users_created',
        'rate_limit_per_minute', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'api_key']
    readonly_fields = ['api_key', 'api_secret', 'total_requests', 'total_users_created', 'created_at', 'updated_at']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'is_active')
        }),
        ('API Credentials', {
            'fields': ('api_key', 'api_secret'),
            'description': 'Bu ma\'lumotlar faqat bir marta ko\'rsatiladi. API Secret hash qilingan holda saqlanadi.'
        }),
        ('Sozlamalar', {
            'fields': ('rate_limit_per_minute',)
        }),
        ('Statistika', {
            'fields': ('total_requests', 'total_users_created')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def save_model(self, request, obj, form, change):
        """Partner yaratilganda credentials generatsiya qilish"""
        if not change:  # Yangi partner
            api_key, api_secret = Partner.generate_credentials()
            obj.api_key = api_key
            obj.api_secret = Partner.hash_secret(api_secret)

            super().save_model(request, obj, form, change)

            # Admin ga xabar ko'rsatish
            from django.contrib import messages
            messages.success(
                request,
                format_html(
                    '<strong>⚠️ IMPORTANT: Bu ma\'lumotlarni saqlang!</strong><br>'
                    'API Key: <code>{}</code><br>'
                    'API Secret: <code>{}</code><br>'
                    '<em>API Secret bir marta ko\'rsatiladi va qayta tiklanmaydi!</em>',
                    api_key,
                    api_secret
                )
            )
        else:
            super().save_model(request, obj, form, change)


@admin.register(PartnerRequest)
class PartnerRequestAdmin(admin.ModelAdmin):
    list_display = [
        'partner', 'endpoint', 'method', 'status_code',
        'user_phone', 'ip_address', 'created_at'
    ]
    list_filter = ['partner', 'method', 'status_code', 'created_at']
    search_fields = ['endpoint', 'user_phone', 'ip_address']
    readonly_fields = [
        'partner', 'endpoint', 'method', 'status_code',
        'user_phone', 'ip_address', 'request_data', 'response_data',
        'created_at'
    ]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        # Partner request qo'lda qo'shib bo'lmaydi
        return False

    def has_change_permission(self, request, obj=None):
        # Partner request o'zgartirib bo'lmaydi
        return False