from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from config.validators import PhoneValidator, normalize_phone
import datetime

today = datetime.date.today()

class UserManager(BaseUserManager):
    def _create_user(self, phone, password=None, **extra_fields):
        phone = normalize_phone(phone)

        user = self.model(phone=phone, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(phone, password, **extra_fields)

class UserModel(AbstractUser):
    username = None
    class Roles(models.TextChoices):
        CLIENT = 'client', 'Client'
        DOCTOR = 'doctor', 'Doctor'
        OPERATOR = 'operator', 'Operator'

    objects = UserManager()

    phone = models.CharField(max_length=20, unique=True, validators=[PhoneValidator()])
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CLIENT)
    email = models.EmailField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    language = models.CharField(max_length=3, default='uz')
    theme_mode = models.SmallIntegerField(choices=((1,'Black'),(2,'White')), default=1)
    notification_key = models.CharField(max_length=255, null=True, blank=True)
    favorite_medicine = models.ManyToManyField('shop.Medicine', blank=True, related_name='fav_users')
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'phone'   # login uchun default field
    REQUIRED_FIELDS = []        # email yoki first_name, last_name optional

    def is_client(self): return self.role == self.Roles.CLIENT
    def is_doctor(self): return self.role == self.Roles.DOCTOR
    def is_operator(self): return self.role == self.Roles.OPERATOR

    def __str__(self): return f"{self.id} | {self.phone} | {self.role}"


# Referrals
class Referrals(models.Model):
    # inviter = models.CharField(max_length=16, db_index=True)
    # invited_user = models.CharField(max_length=16, db_index=True)

    user = models.ForeignKey(UserModel, unique=False, on_delete=models.DO_NOTHING, related_name='referrals')
    # invited_user = models.ForeignKey(UserModel, unique=False, on_delete=models.DO_NOTHING)
    invited_user = models.CharField(max_length=256)


# Sms kode
class SmsCode(models.Model):
    PURPOSE_CHOICES = (
        ('register', 'Register account'),
        ('reset_password', 'Reset password'),
    )

    phone = models.CharField(max_length=16, db_index=True)
    ip = models.GenericIPAddressField(db_index=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    expire_at = models.DateTimeField(db_index=True)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        index_together = []
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['expire_at']),
        ]

    def __str__(self):
        return f"{self.phone}: {self.code} ({self.expire_at})"


# Sms try
class SmsAttempt(models.Model):
    phone = models.CharField(max_length=16, db_index=True)
    counter = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(db_index=True)

    def __str__(self):
        return f"{self.phone}: {self.counter} pcs. attempts"


class CountyModel(models.Model):
    name = models.CharField(max_length=100)
    order_number = models.PositiveIntegerField(null=True, editable=True)

    def __str__(self):
        return self.name


class RegionModel(models.Model):
    country = models.ForeignKey(CountyModel, on_delete=models.RESTRICT)
    name = models.CharField(max_length=100)
    delivery_price = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.name


# class DeliveryAddress(models.Model):
#     user = models.ForeignKey(UserModel, on_delete=models.RESTRICT)
#     name = models.CharField(max_length=255, null=True, blank=True)
#     region = models.ForeignKey(RegionModel, on_delete=models.RESTRICT, null=True)
#     full_address = models.CharField(max_length=255, null=True, blank=True)
#     apartment_office = models.CharField(max_length=255, null=True, blank=True)
#     floor = models.CharField(max_length=255, null=True, blank=True)
#     door_or_phone = models.CharField(max_length=255, null=True, blank=True)
#     instructions = models.CharField(max_length=255, null=True, blank=True)
# 
#     def __str__(self):
#         return f"{self.user}'s delivery address: {self.region}, {self.full_address}, {self.apartment_office} {self.floor} floor, {self.door_or_phone}"


class OfferModel(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    offer = models.TextField()

    def __str__(self):
        return f"{self.name} offer for {self.phone_number} ({self.email})"
