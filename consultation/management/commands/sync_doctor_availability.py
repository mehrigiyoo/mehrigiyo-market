from django.core.management.base import BaseCommand
from specialist.models import Doctor
from consultation.models import DoctorAvailability, GlobalAvailabilityTemplate


class Command(BaseCommand):
    help = 'Sync availability slots for all verified doctors from GlobalAvailabilityTemplate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--doctor-id',
            type=int,
            help='Sync only for specific doctor ID',
        )

    def handle(self, *args, **options):
        doctor_id = options.get('doctor_id')

        # Get doctors
        if doctor_id:
            doctors = Doctor.objects.filter(
                id=doctor_id,
                is_verified=True,
                user__is_approved=True,
                user__role='doctor'  # ← MUHIM: Faqat doctor role
            ).select_related('user')
        else:
            doctors = Doctor.objects.filter(
                is_verified=True,
                user__is_approved=True,
                user__role='doctor'  # ← MUHIM: Faqat doctor role
            ).select_related('user')

        if not doctors.exists():
            self.stdout.write(self.style.WARNING('No verified doctors found'))
            return

        # Get all active templates
        templates = GlobalAvailabilityTemplate.objects.filter(is_active=True)

        if not templates.exists():
            self.stdout.write(self.style.WARNING('No active GlobalAvailabilityTemplate found'))
            return

        self.stdout.write(f'Found {doctors.count()} doctors and {templates.count()} templates')

        # Sync for each doctor
        total_created = 0
        total_skipped = 0

        for doctor in doctors:
            doctor_created = 0
            doctor_skipped = 0

            for template in templates:
                # Check if slot already exists
                exists = DoctorAvailability.objects.filter(
                    doctor=doctor.user,
                    date=template.date,
                    start_time=template.start_time,
                    end_time=template.end_time
                ).exists()

                if exists:
                    doctor_skipped += 1
                    continue

                # Create slot
                DoctorAvailability.objects.create(
                    doctor=doctor.user,
                    template=template,
                    date=template.date,
                    start_time=template.start_time,
                    end_time=template.end_time,
                    is_available=True
                )
                doctor_created += 1

            total_created += doctor_created
            total_skipped += doctor_skipped

            self.stdout.write(
                f"  Doctor: {doctor.full_name} (ID: {doctor.id}) - "
                f"Created: {doctor_created}, Skipped: {doctor_skipped}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Total: Created {total_created} slots, Skipped {total_skipped} existing slots'
            )
        )