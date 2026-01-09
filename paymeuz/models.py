from django.db import models
from django.utils.translation import gettext_lazy as _
from account.models import UserModel
from paymeuz.keywords import PAYME_PAYMENT_STATUS, TYPES


class PaymeTransactionModel(models.Model):
    _id = models.CharField(max_length=255, verbose_name=_('transaction id'), null=True, blank=True)
    request_id = models.IntegerField(verbose_name=_('request id'))
    order_id = models.IntegerField(verbose_name=_('order id'))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('amount'))
    state = models.IntegerField(blank=True, null=True, verbose_name=_('state'))
    status = models.CharField(choices=PAYME_PAYMENT_STATUS, default='processing', max_length=55,
                              verbose_name=_('status'))
    _type = models.CharField(choices=TYPES, default='PAYMENT', max_length=55, verbose_name=_('type'))
    phone = models.CharField(max_length=20, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=_('create time'))
    perform_time = models.BigIntegerField(default=0, verbose_name=_('perform time'))
    cancel_time = models.BigIntegerField(default=0, verbose_name=_('cancel time'))
    cancel_reason = models.IntegerField(null=True, blank=True, verbose_name=_('cancel reason'))

    def __str__(self):
        return f"{self.phone}'s ID{self.id} payment"

    class Meta:
        verbose_name = _('payme transaction')
        verbose_name_plural = _('payme transactions')


class Card(models.Model):
    owner = models.ForeignKey(UserModel, on_delete=models.RESTRICT)
    number = models.CharField(max_length=16)
    expire = models.CharField(max_length=5)
    token = models.TextField()
    recurrent = models.BooleanField()
    verify = models.BooleanField()
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.owner}'s card {self.number} {self.expire}"
