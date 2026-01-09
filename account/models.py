from django.core.validators import EmailValidator
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from config.validators import PhoneValidator
from shop.models import Medicine
from specialist.models import Doctor
import datetime

# from django.utils.translation import gettext as _

today = datetime.date.today()


class UserManager(BaseUserManager):

    def __create_user(self, username, password, **kwargs):
        username = PhoneValidator.clean(username)
        validator = PhoneValidator()
        validator(username)

        user = UserModel(**kwargs)
        user.username = username
        user.set_password(password)
        user.save()

    def create_user(self, *args, **kwargs):
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)

        if kwargs.get('is_staff') or kwargs.get('is_superuser'):
            raise Exception("User is_staff=False va is_superuser=False bo'lishi shart!")

        return self.__create_user(*args, **kwargs)

    def create_superuser(self, *args, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)

        if not kwargs.get('is_staff') or not kwargs.get('is_superuser'):
            raise Exception("User is_staff=True va is_superuser=True bo'lishi shart!")

        return self.__create_user(*args, **kwargs)


class UserModel(AbstractUser):
    objects = UserManager()
    #    username = models.CharField(max_length=15, unique=True, help_text="Пожалуйста, укажите свой пароль")
    username = models.CharField(max_length=256, unique=True,validators=[PhoneValidator()],
                                help_text="Пожалуйста, укажите свой пароль")
    password = models.CharField(max_length=256, null=True, blank=True)
    email = models.EmailField(validators=[EmailValidator()], null=True, blank=True)
    avatar = models.ImageField(upload_to=f'avatars/{today.year}-{today.month}-{today.month}/', null=True, blank=True)
    address = models.ForeignKey('RegionModel', on_delete=models.RESTRICT, null=True, blank=True)
    language = models.CharField(max_length=3, null=True, blank=True)
    favorite_medicine = models.ManyToManyField(Medicine, blank=True, related_name='fav_med')
    favorite_doctor = models.ManyToManyField(Doctor, blank=True, related_name='fav_dock')

    # referrals = models.ManyToManyField(Referrals, blank=True, related_name='referrals')

    WHITE = 1
    BLACK = 2
    USER_THEMES = [
        WHITE,
        BLACK
    ]
    theme_mode = models.SmallIntegerField(choices=(
        (BLACK, 'Black'),
        (WHITE, 'White')
    ), default=1, db_index=True)

    specialist_doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT,
                                          null=True, blank=True, related_name='worker')
    doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT, null=True)

    notificationKey = models.CharField(max_length=255, null=True, blank=True)
    username_validator = PhoneValidator()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return f"ID{self.id} {self.username}"


# Referrals
class Referrals(models.Model):
    # inviter = models.CharField(max_length=16, db_index=True)
    # invited_user = models.CharField(max_length=16, db_index=True)

    user = models.ForeignKey(UserModel, unique=False, on_delete=models.DO_NOTHING, related_name='referrals')
    # invited_user = models.ForeignKey(UserModel, unique=False, on_delete=models.DO_NOTHING)
    invited_user = models.CharField(max_length=256)


# Sms kode
class SmsCode(models.Model):
    phone = models.CharField(max_length=16, db_index=True)
    ip = models.GenericIPAddressField(db_index=True)
    code = models.CharField(max_length=10)
    expire_at = models.DateTimeField(db_index=True)
    confirmed = models.BooleanField(default=False)

    class Meta:
        index_together = []

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


class DeliveryAddress(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.RESTRICT)
    name = models.CharField(max_length=255, null=True, blank=True)
    region = models.ForeignKey(RegionModel, on_delete=models.RESTRICT, null=True)
    full_address = models.CharField(max_length=255, null=True, blank=True)
    apartment_office = models.CharField(max_length=255, null=True, blank=True)
    floor = models.CharField(max_length=255, null=True, blank=True)
    door_or_phone = models.CharField(max_length=255, null=True, blank=True)
    instructions = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user}'s delivery address: {self.region}, {self.full_address}, {self.apartment_office} {self.floor} floor, {self.door_or_phone}"


class OfferModel(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    offer = models.TextField()

    def __str__(self):
        return f"{self.name} offer for {self.phone_number} ({self.email})"
