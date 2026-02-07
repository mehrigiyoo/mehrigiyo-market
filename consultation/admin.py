from datetime import time, timedelta, date

from django.contrib import admin
from django.utils.html import format_html
from .models import ConsultationRequest, DoctorAvailability, GlobalAvailabilityTemplate


@admin.register(GlobalAvailabilityTemplate)
class GlobalAvailabilityTemplateAdmin(admin.ModelAdmin):
    """
    Global availability - Admin creates ONCE for ALL doctors
    """

    list_display = [
        'id',
        'date_display',
        'time_range',
        'active_badge',
        'doctors_count',
        'created_at'
    ]

    list_filter = ['is_active', 'date']
    date_hierarchy = 'date'

    fieldsets = (
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time'),
            'description': 'This will apply to ALL approved doctors automatically'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    readonly_fields = ['created_at', 'created_by']

    actions = ['generate_week_templates', 'regenerate_doctor_slots']

    def date_display(self, obj):
        day_name = obj.date.strftime('%A')
        return f"{obj.date} ({day_name})"

    date_display.short_description = 'Date'

    def time_range(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"

    time_range.short_description = 'Time'

    def active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )

    active_badge.short_description = 'Status'

    def doctors_count(self, obj):
        """Show how many doctors have this slot"""
        count = obj.doctor_slots.count()
        available = obj.doctor_slots.filter(is_available=True).count()
        return f"{available}/{count} available"

    doctors_count.short_description = 'Doctors'

    def save_model(self, request, obj, form, change):
        """Set created_by"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def generate_week_templates(self, request, queryset):
        """
        Generate 1 week of global templates

        Creates:
        - 7 days (today + 6)
        - 9 time slots per day
        - Automatically generates for ALL doctors
        """
        start_date = date.today()

        time_slots = [
            (time(9, 0), time(10, 0)),
            (time(10, 0), time(11, 0)),
            (time(11, 0), time(12, 0)),
            (time(12, 0), time(13, 0)),
            (time(13, 0), time(14, 0)),
            (time(14, 0), time(15, 0)),
            (time(15, 0), time(16, 0)),
            (time(16, 0), time(17, 0)),
            (time(17, 0), time(18, 0)),
        ]

        templates_created = 0
        doctor_slots_created = 0

        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)

            for start_time, end_time in time_slots:
                template, created = GlobalAvailabilityTemplate.objects.get_or_create(
                    date=current_date,
                    start_time=start_time,
                    defaults={
                        'end_time': end_time,
                        'is_active': True,
                        'created_by': request.user
                    }
                )

                if created:
                    templates_created += 1
                    # Auto-generates doctor slots via model.save()
                    doctor_slots_created += template.doctor_slots.count()

        self.message_user(
            request,
            f"✅ Created {templates_created} global templates → "
            f"{doctor_slots_created} doctor slots auto-generated"
        )

    generate_week_templates.short_description = "📅 Generate 1 week (for ALL doctors)"

    def regenerate_doctor_slots(self, request, queryset):
        """
        Regenerate doctor slots from templates

        Use when new doctors are approved
        """
        total_created = 0

        for template in queryset:
            count = template.generate_for_all_doctors()
            total_created += count

        self.message_user(
            request,
            f"✅ Regenerated {total_created} doctor slots from {queryset.count()} templates"
        )

    regenerate_doctor_slots.short_description = "🔄 Regenerate doctor slots"


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    """
    Per-doctor availability (auto-generated, read-only mostly)
    """

    list_display = [
        'id',
        'doctor_name',
        'user_role',
        'date_display',
        'time_range',
        'status_badge',
        'from_template',
    ]

    list_filter = ['is_available', 'date', 'doctor', 'template']
    search_fields = ['doctor__first_name', 'doctor__phone']
    date_hierarchy = 'date'

    fieldsets = (
        ('Doctor', {
            'fields': ('doctor', 'template')
        }),
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('is_available', 'consultation')
        }),
    )

    readonly_fields = ['template', 'consultation', 'created_at']

    def user_role(self, obj):
        return obj.doctor.get_role_display() if hasattr(obj.doctor, 'get_role_display') else obj.doctor.role

    def doctor_name(self, obj):
        return obj.doctor.first_name or obj.doctor.phone

    doctor_name.short_description = 'Doctor'

    def date_display(self, obj):
        return obj.date.strftime('%Y-%m-%d (%a)')

    date_display.short_description = 'Date'

    def time_range(self, obj):
        return f"{obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')}"

    time_range.short_description = 'Time'

    def status_badge(self, obj):
        if obj.is_available:
            return format_html(
                '<span style="background-color: green; color: white; '
                'padding: 3px 8px; border-radius: 3px;">Available</span>'
            )
        return format_html(
            '<span style="background-color: orange; color: white; '
            'padding: 3px 8px; border-radius: 3px;">Booked</span>'
        )

    status_badge.short_description = 'Status'

    def from_template(self, obj):
        if obj.template:
            return "✅ Auto-generated"
        return "➕ Manual"

    from_template.short_description = 'Source'

    def has_add_permission(self, request):
        # Discourage manual creation (use templates instead)
        return False


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'client_phone',
        'doctor_name',
        'date_time',
        'status_badge'
    ]

    list_filter = ['status', 'requested_date']
    search_fields = ['client__phone', 'doctor__first_name']

    def client_phone(self, obj):
        return obj.client.phone

    def doctor_name(self, obj):
        return obj.doctor.first_name or obj.doctor.phone

    def date_time(self, obj):
        return f"{obj.requested_date} {obj.requested_time.strftime('%H:%M')}"

    def status_badge(self, obj):
        colors = {
            'created': 'gray',
            'paid': 'blue',
            'accepted': 'green',
            'completed': 'darkgreen',
            'cancelled': 'red',
        }

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.status.upper()
        )

    status_badge.short_description = 'Status'
