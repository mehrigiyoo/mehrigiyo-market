from django.core.management.base import BaseCommand
from consultation.models import DoctorAvailability


class Command(BaseCommand):
    help = 'Clean up DoctorAvailability slots for users with role != "doctor"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # Get all slots
        all_slots = DoctorAvailability.objects.select_related('doctor').all()

        # Find slots for non-doctor users
        invalid_slots = []
        for slot in all_slots:
            if slot.doctor.role != 'doctor':
                invalid_slots.append(slot)

        if not invalid_slots:
            self.stdout.write(self.style.SUCCESS('✅ No invalid slots found. All slots are for doctors.'))
            return

        self.stdout.write(self.style.WARNING(f'Found {len(invalid_slots)} invalid slots:'))

        # Group by user role
        by_role = {}
        for slot in invalid_slots:
            role = slot.doctor.role
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(slot)

        for role, slots in by_role.items():
            self.stdout.write(f"  - Role '{role}': {len(slots)} slots")
            # Show sample users
            users = set([slot.doctor for slot in slots[:5]])
            for user in users:
                self.stdout.write(f"    User ID {user.id}: {user.first_name or user.phone} (role: {user.role})")

        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN - Nothing deleted. Run without --dry-run to delete.'))
            return

        # Delete invalid slots
        count = len(invalid_slots)
        for slot in invalid_slots:
            slot.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Deleted {count} invalid slots from non-doctor users'
            )
        )