import datetime

from django.db.models import Avg
from specialist.models import Doctor, AdviceTime, WorkSchedule


def get_doctors_queryset(filters):
    return (
        Doctor.objects
        .annotate(total_rate=Avg('comments_doc__rate'))
        .filter(**filters)
        .select_related()
        .prefetch_related()
        .order_by('-total_rate')
    )


def get_advice_queryset(*, user=None, doctor_id=None, day=None, month=None, year=None, my=False):
    """
    AdviceTime uchun queryset olish
    """
    qs = AdviceTime.objects.all()

    if doctor_id:
        qs = qs.filter(doctor_id=doctor_id)

    if day and month and year:
        qs = qs.filter(
            start_time__day=day,
            start_time__month=month,
            start_time__year=year
        )
    else:
        qs = qs.filter(start_time__gte=datetime.datetime.now())

    if my and user:
        qs = qs.filter(client=user)

    return qs


def get_advice_times(filters):
    """
    Filters bo'yicha AdviceTime olish
    """
    return AdviceTime.objects.filter(**filters)


def get_available_slots(doctor_id, date):
    """
    Berilgan kunda doctor uchun bo'sh slotlarni olish
    """
    weekday = date.weekday()
    work_periods = WorkSchedule.objects.filter(doctor_id=doctor_id, weekday=weekday)
    unavailable = AdviceTime.objects.filter(
        doctor_id=doctor_id,
        start_time__date=date
    )

    slots = []
    for period in work_periods:
        start = datetime.datetime.combine(date, period.start_time)
        end = datetime.datetime.combine(date, period.end_time)
        current = start
        while current + datetime.timedelta(minutes=30) <= end:
            slot_end = current + datetime.timedelta(minutes=30)
            # Band slotlarni chiqarib tashla
            if not unavailable.filter(start_time__lt=slot_end, end_time__gt=current).exists():
                slots.append({'start_time': current, 'end_time': slot_end})
            current = slot_end
    return slots
