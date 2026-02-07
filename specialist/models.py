from django.db import models

from account.models import UserModel


class TypeDoctor(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=f'types/', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_doctors_count(self):
        return Doctor.objects.filter(type_doctor=self).count()

# Doctor model change gender,birthday,
class Doctor(models.Model):
    user = models.OneToOneField(
        'account.UserModel',
        on_delete=models.CASCADE,
        related_name='doctor'
    )

    image = models.ImageField(upload_to='doctors/', default='defaults/doctor.jpg')
    full_name = models.CharField(max_length=255)
    experience = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    type_doctor = models.ForeignKey(TypeDoctor, on_delete=models.RESTRICT)
    top = models.BooleanField(default=False)
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=(('male', 'Male'), ('female', 'Female'))
    )

    consultation_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50000,
        help_text="Consultation price in UZS (Set by admin)"
    )

    average_rating = models.FloatField(default=0)      # 4.6
    rating_count = models.PositiveIntegerField(default=0)  # 128 ta baho
    view_count = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Doctor: {self.full_name}"

class DoctorRating(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user = models.ForeignKey(
        'account.UserModel',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'client'}
    )

    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'user'],
                name='unique_doctor_user_rating'
            )
        ]

    def __str__(self):
        return f'{self.doctor} - {self.rating}'


class DoctorView(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    user = models.ForeignKey('account.UserModel', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'user'],
                name='unique_doctor_view'
            )
        ]

class DoctorVerification(models.Model):
    doctor = models.OneToOneField(
        Doctor,
        on_delete=models.CASCADE,
        related_name='verification'
    )

    diploma = models.FileField(upload_to='doctor_docs/diplomas/')
    # passport = models.FileField(upload_to='doctor_docs/passports/', null=True, blank=True)

    license_number = models.CharField(max_length=100, null=True, blank=True)
    license_expire_date = models.DateField(null=True, blank=True)

    workplace = models.CharField(max_length=255, blank=True)

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    admin_comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)



FEEDBACK = (
    (1, 'Not Bad'),
    (2, 'Love it'),
    (3, 'Nice Work'),
    (4, 'Awesome'),
)


class RateDoctor(models.Model):
    client = models.ForeignKey(
        'account.UserModel',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'client'}
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    rate = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    feedback = models.PositiveSmallIntegerField(choices=FEEDBACK)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['client', 'doctor'],
                name='unique_client_doctor_rating'
            )
        ]

# class AdviceStatus(models.TextChoices):
#     PENDING = 'pending'
#     CONFIRMED = 'confirmed'
#     CANCELED = 'canceled'
#     FINISHED = 'finished'


class AdviceTime(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT)
    client = models.ForeignKey('account.UserModel', on_delete=models.RESTRICT)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    # status = models.CharField(
    #     max_length=20,
    #     choices=AdviceStatus.choices,
    #     default=AdviceStatus.PENDING,
    #     db_index=True
    # )

    def __str__(self):
        return f"{self.doctor}'s advice time for {self.client} from {self.start_time} to {self.end_time}"


class Advertising(models.Model):
    image = models.ImageField(upload_to=f'doctor/advertising/', null=True, blank=True)
    title = models.CharField(max_length=255)
    text = models.TextField()
    is_active = models.BooleanField(default=True, db_index=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT, null=True, blank=True)

    def __str__(self):
        if self.doctor:
            return f"Ad for {self.doctor.full_name}: {self.title}"
        return f"General Ad: {self.title}"


class WorkSchedule(models.Model):
    """
    Doctorning haftalik ish jadvali
    """
    WEEKDAYS = (
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='work_schedules')
    weekday = models.IntegerField(choices=WEEKDAYS)  # Hafta kuni
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('doctor', 'weekday', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.doctor.full_name} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class DoctorUnavailable(models.Model):
    """
    Doctor ishlay olmaydigan kunlar
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='unavailable_days')
    date = models.DateField()

    class Meta:
        unique_together = ('doctor', 'date')

    def __str__(self):
        return f"{self.doctor.full_name} unavailable on {self.date}"
