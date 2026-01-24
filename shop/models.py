import datetime

from django.db import models
today = datetime.date.today()

class TypeMedicine(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=f'types/', null=True, blank=True)
    icon = models.ImageField(upload_to=f'types/icons/', null=True, blank=True)

    def __str__(self):
        return self.name


class Medicine(models.Model):
    image = models.ImageField(upload_to=f'medicine/', null=True, blank=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    order_count = models.IntegerField(default=0)
    description = models.TextField(null=True)
    quantity = models.IntegerField(default=0)
    review = models.IntegerField(default=0)
    weight = models.FloatField(default=0)
    type_medicine = models.ForeignKey(TypeMedicine, on_delete=models.RESTRICT, null=True)
    cost = models.IntegerField(null=True)
    discount = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now=True, null=True)

    product_inn = models.CharField(max_length=255, blank=True, null=True)
    product_ikpu = models.CharField(max_length=255, blank=True, null=True)
    product_package_code = models.CharField(max_length=255, blank=True, null=True)

    content_uz = models.TextField(null=True)
    content_ru = models.TextField(null=True)
    content_en = models.TextField(null=True)

    features_uz = models.TextField(null=True)
    features_ru = models.TextField(null=True)
    features_en = models.TextField(null=True)

    certificates_uz = models.TextField(null=True)
    certificates_ru = models.TextField(null=True)
    certificates_en = models.TextField(null=True)

    application_uz = models.TextField(null=True)
    application_ru = models.TextField(null=True)
    application_en = models.TextField(null=True)

    contraindications_uz = models.TextField(null=True)
    contraindications_ru = models.TextField(null=True)
    contraindications_en = models.TextField(null=True)


    def __str__(self):
        return self.name

class PicturesMedicine(models.Model):
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.CASCADE,
        related_name='pictures'
    )
    image = models.ImageField(
        upload_to=f'medicine_pictures/{today.year}-{today.month}-{today.month}/',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.medicine.name} - {self.id}"



class CartModel(models.Model):
    class Status(models.IntegerChoices):
        ACTIVE = 1, 'active'
        DONE = 2, 'done'
        DELETED = 3

    user = models.ForeignKey(
        'account.UserModel',
        on_delete=models.CASCADE,
        related_name='carts'
    )
    product = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name='cart_items'
    )
    amount = models.PositiveIntegerField(default=1)
    status = models.SmallIntegerField(
        choices=Status.choices,
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        price = self.product.cost or 0
        discount_percent = self.product.discount or 0
        discount_amount = price * discount_percent / 100
        return (price - discount_amount) * self.amount

    class Meta:
        unique_together = ('user', 'product', 'status')
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user} | {self.product} | {self.amount}"


PAYMENT_TYPES = (
    (1, 'Оплата при доставке'),
    (2, 'Кредитная карта'),
    (3, 'Прямой банковский перевод'),
)

PAYMENT_STATUS = (
    (1, 'В ожидании'),
    (2, 'Ошибка'),
    (3, 'Завершено'),
    (4, 'Отменен'),
    (5, 'Истёк'),
    (6, 'Возвращен'),
)

DELIVERY_STATUS = (
    (1, 'В ожидании'),
    (2, 'На доставке'),
    (3, 'Доставлен'),
    (4, 'Возвращен'),
)


class DeliveryMan(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class OrderModel(models.Model):
    user = models.ForeignKey('account.UserModel', on_delete=models.RESTRICT, null=True)
    credit_card = models.ForeignKey('paymeuz.Card', on_delete=models.RESTRICT, null=True)
    shipping_address = models.ForeignKey('account.DeliveryAddress', on_delete=models.RESTRICT, null=True, blank=True)
    cart_products = models.ManyToManyField(CartModel)
    price = models.IntegerField(null=True)
    payment_type = models.PositiveSmallIntegerField(choices=PAYMENT_TYPES, default=2)
    payment_status = models.PositiveSmallIntegerField(choices=PAYMENT_STATUS, default=1)
    delivery_status = models.PositiveSmallIntegerField(choices=DELIVERY_STATUS, default=1)
    delivery = models.ForeignKey(DeliveryMan, on_delete=models.RESTRICT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_payme_amount(self):
        return self.price * 100

    def __str__(self):
        return self.user.get_full_name()


FEEDBACK_TYPES = (
    ('feedback_client', 'Mijozlar izohi'),
    ('feedback_product', 'Mahsulot izohi'),
    ('product_instruction', 'Mahsulot qo\'llanmasi')
)

FEEDBACK_CATEGORIES = (
    ('feedback_client', 'Mijozlar izohi'),
    ('feedback_celebrities', 'Mashxurlar izohi'),
    ('feedback_specialists', 'Mutahassislar izohi')
)


class Feedbacks(models.Model):
    link = models.URLField(null=True, blank=True)
    medicine = models.ForeignKey(Medicine, on_delete=models.RESTRICT, null=True, blank=True, related_name="feedbacks")
    type = models.CharField(choices=FEEDBACK_TYPES, max_length=75, blank=True, default='feedback_client')
    category = models.CharField(choices=FEEDBACK_CATEGORIES, max_length=75, blank=True, default='feedback_client')


