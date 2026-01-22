from django.db.models import F, Avg, Count
from rest_framework.exceptions import ValidationError
import uuid
import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import AdviceTime, Doctor, WorkSchedule, DoctorUnavailable
from chat.models import ChatRoom
from account.models import UserModel
from specialist.methods import notify_doctors


def increment_review_count(queryset):
    queryset.update(review=F('review') + 1)


def check_doctor_availability(doctor_id, start_time, end_time):
    """
    Doctor belgilangan vaqtda mavjud yoki yo'qligini tekshiradi
    """
    # Doctor ishlay olmaydigan kunlarni tekshir
    if DoctorUnavailable.objects.filter(doctor_id=doctor_id, date=start_time.date()).exists():
        raise ValidationError("Doktor ushbu kunda ishlamaydi!")

    # Doctor haftalik ish jadvali bo'yicha tekshir
    weekday = start_time.weekday()
    work_periods = WorkSchedule.objects.filter(doctor_id=doctor_id, weekday=weekday)

    if not any(w.start_time <= start_time.time() < w.end_time and w.start_time < end_time.time() <= w.end_time for w in
               work_periods):
        raise ValidationError("Doktor ushbu vaqtda ishlamaydi!")

    # Band vaqt tekshirish
    if AdviceTime.objects.filter(
            doctor_id=doctor_id,
            start_time__lt=end_time,
            end_time__gt=start_time
    ).exists():
        raise ValidationError("Doktor bu vaqt oralig'ida band!")


@transaction.atomic
def create_advice_service(*, client, doctor_id, start_time, end_time):
    #  Band vaqt tekshirish (race-condition safe)
    if AdviceTime.objects.filter(
        doctor_id=doctor_id,
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists():
        raise Exception("Doktor bu vaqt oralig'ida band!")

    # Advice yaratish
    advice = AdviceTime.objects.create(
        client=client,
        doctor_id=doctor_id,
        start_time=start_time,
        end_time=end_time
    )

    # Telegram notify
    TIME_FORMAT = "%d/%m/%Y %H:%M"
    start = datetime.datetime.fromisoformat(start_time.replace('Z', '+05:00')).strftime(TIME_FORMAT)
    end = datetime.datetime.fromisoformat(end_time.replace('Z', '+05:00')).strftime(TIME_FORMAT)
    notify_doctors(advice.id, start_time=start, end_time=end)

    # Chat yaratish
    doctor_user = UserModel.objects.get(specialist_doctor_id=doctor_id, is_staff=True)
    ChatRoom.objects.get_or_create(client=client, doktor=doctor_user, defaults={'token': uuid.uuid4()})

    return advice



def update_doctor_rating(doctor: Doctor):
    stats = doctor.ratings.aggregate(
        avg=Avg('rating'),
        count=Count('id')
    )

    doctor.average_rating = round(stats['avg'] or 0, 2)
    doctor.rating_count = stats['count']
    doctor.save(update_fields=['average_rating', 'rating_count'])
