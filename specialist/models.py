from django.db import models
from config.settings import BASE_DIR


class TypeDoctor(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=f'types/', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_doctors_count(self):
        sum = Doctor.objects.filter(type_doctor=self)
        return len(sum)

# Doctor model change gender,birthday,
class Doctor(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    image = models.ImageField(upload_to=f'doctor/', blank=True, default='defaults/60111.jpg')
    #  default=BASE_DIR /'60111.jpg')
    full_name = models.CharField(max_length=255, null=True)
    review = models.IntegerField(default=0)
    experience = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)
    type_doctor = models.ForeignKey(TypeDoctor, on_delete=models.RESTRICT, null=True)
    created_at = models.DateTimeField(auto_now=True, null=True)
    birthday = models.DateField(null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="male")

    def __str__(self):
        return self.full_name


FEEDBACK = (
    (1, 'Not Bad'),
    (2, 'Love it'),
    (3, 'Nice Work'),
    (4, 'Awesome'),
)


class RateDoctor(models.Model):
    client = models.ForeignKey('account.UserModel', on_delete=models.RESTRICT)
    doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT)
    rate = models.SmallIntegerField(default=4, choices=((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')))
    feedback = models.SmallIntegerField(default=1, choices=FEEDBACK)
    created_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.client}'s rate for {self.doctor} is {self.rate}"


class AdviceTime(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT)
    client = models.ForeignKey('account.UserModel', on_delete=models.RESTRICT)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.doctor}'s advice time for {self.client} from {self.start_time} to {self.end_time}"


class Advertising(models.Model):
    image = models.ImageField(upload_to=f'doctor/advertising/', null=True, blank=True)
    title = models.CharField(max_length=255)
    text = models.TextField()
    doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT, null=True, blank=True)

    def __str__(self):
        return f"{self.doctor}'s advertisement: {self.title} ({self.text})"
