from celery import shared_task
from datetime import date, timedelta, time
from .models import DoctorAvailability
from specialist.models import Doctor


@shared_task
def generate_weekly_availability():
    """
    Auto-generate availability for next week

    Runs: Every Sunday at 00:00
    Generates: Next 7 days for all doctors
    """
    doctors = Doctor.objects.filter(
        is_verified=True,
        user__is_approved=True
    ).select_related('user')

    start_date = date.today() + timedelta(days=7)  # Next week

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

    count = 0

    for doctor in doctors:
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)

            for start_time, end_time in time_slots:
                obj, created = DoctorAvailability.objects.get_or_create(
                    doctor=doctor.user,
                    date=current_date,
                    start_time=start_time,
                    defaults={'end_time': end_time}
                )

                if created:
                    count += 1

    print(f"✅ Generated {count} slots")