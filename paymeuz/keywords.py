from django.conf import settings
from django.utils.translation import gettext_lazy as _

ORDER_NOT_FOUND = -31050
TRANSACTION_NOT_FOUND = -31003
UNABLE_TO_PERFORM_OPERATION = -31008
INVALID_AMOUNT = -31001
ORDER_FOUND = 200
AUTH_FAILED = -32504
ORDER_BUSY = -31050
SMS_NOT_CONNECTED = -31301
CARD_NOT_WORKING = -31900
SYSTEM_ERROR = -32400
INVALID_CODE = -31103
TIME_OUT = -31101
MORE_THAN_ALLOWED = -31612

CREATE_TRANSACTION = 1
CLOSE_TRANSACTION = 2
CANCEL_CREATE_TRANSACTION = -1
CANCEL_CLOSE_TRANSACTION = -2

TIME_OUT_MESSAGE = {
    "uz": "Kod muddati tugagan. Yangi kod talab qiling.",
    "ru": "Время жизни кода истекло. Запросите новый код.",
    "en": "Code has expired. Request a new code."
}

INVALID_CODE_MESSAGE = {
    "uz": "Yaroqsiz kod kiritildi.",
    "ru": "Введен неверный код.",
    "en": "Invalid code entered."
}

SYSTEM_ERROR_MESSAGE = {
    "uz": "Systemada xatolik. Tasdiqlash kodi ketmadi",
    "ru": "Системная ошибка. Код подтверждения не может быть отправлен",
    "en": "System error. Verify code can't send"
}

SMS_NOT_CONNECTED_MESSAGE = {
    "uz": "Не подключено смс-информирование",
    "ru": "Не подключено смс-информирование",
    "en": "Не подключено смс-информирование"
}

CARD_NOT_WORKING_MESSAGE = {
    "uz": "Ushbu turdagi karta qo'llab-quvvatlanmaydi",
    "ru": "Данный тип карты не обслуживается.",
    "en": "This type of card is not supported"
}

AUTH_FAILED_MESSAGE = {
    "uz": "Authorization failed",
    "ru": "Authorization failed",
    "en": "Authorization failed"
}

ORDER_BUSY_MESSAGE = {
    "uz": "Order is occupied with other transaction",
    "ru": "Order is occupied with other transaction",
    "en": "Order is occupied with other transaction"
}

ORDER_NOT_FOUND_MESSAGE = {
    'uz': 'Buyurtma topilmadi',
    'ru': 'Заказ не найден',
    'en': 'Order not found'
}
TRANSACTION_NOT_FOUND_MESSAGE = {
    'uz': 'Tranzaksiya topilmadi',
    'ru': 'Транзакция не найдена',
    'en': 'Transaction not found'
}
UNABLE_TO_PERFORM_OPERATION_MESSAGE = {
    'uz': 'Ushbu amalni bajarib bo\'lmaydi',
    'ru': 'Невозможно выполнить данную операцию',
    'en': 'Unable to perform operation'
}
INVALID_AMOUNT_MESSAGE = {
    'uz': 'Miqdori notog\'ri',
    'ru': 'Неверная сумма',
    'en': 'Invalid amount'
}

PROCESSING = 'processing'
SUCCESS = 'success'
FAILED = 'failed'
CANCELED = 'canceled'

PAYMENT = 'payment'
REFERRAL = 'referral'

PAYME_PAYMENT_STATUS = (
    (PROCESSING, _('processing')),
    (SUCCESS, _('success')),
    (FAILED, _('failed')),
    (CANCELED, _('canceled')),
)

TYPES = (
    (PAYMENT, _('payment')),
    (REFERRAL, _('referral'))
)

assert settings.PAYMEUZ_SETTINGS.get('TEST_ENV') is not None
assert settings.PAYMEUZ_SETTINGS.get('ID') is not None
assert settings.PAYMEUZ_SETTINGS.get('ACCOUNTS') is not None
assert settings.PAYMEUZ_SETTINGS['ACCOUNTS'].get('KEY_1') is not None

TELEGRAM_BOT_TOKEN = "7144853422:AAG0xXUPgELDWbU9H7Ey1t1B9r7JdsjAubA"
TELEGRAM_PAYLOAD_URL = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN
TELEGRAM_ORDERS_GROUP_ID = "-1002051666357"
TELEGRAM_CONSULTATION_GROUP_ID = "-1002188309084"
TELEGRAM_CHAT_GROUP_ID = "-1002178046319"

TG_SEND_MESSAGE = TELEGRAM_PAYLOAD_URL + "/sendMessage"
TG_SEND_VIDEO = TELEGRAM_PAYLOAD_URL + "/sendVideo"
TG_SEND_PHOTO = TELEGRAM_PAYLOAD_URL + "/sendPhoto"
TG_SEND_FILE = TELEGRAM_PAYLOAD_URL + "/sendDocument"

TEST_ENV = settings.PAYMEUZ_SETTINGS['TEST_ENV']
TOKEN = settings.PAYMEUZ_SETTINGS['ID']
AUTHORIZATION = {'X-Auth': settings.PAYMEUZ_SETTINGS['ID']}
AUTHORIZATION_TRANSACTION = {'X-Auth': settings.PAYMEUZ_SETTINGS['ID'] + ':' + settings.PAYMEUZ_SETTINGS['KEY']}
KEY_1 = settings.PAYMEUZ_SETTINGS['ACCOUNTS']['KEY_1']
KEY_2 = settings.PAYMEUZ_SETTINGS['ACCOUNTS'].get('KEY_2', 'order_type')
ACCOUNTS = settings.PAYMEUZ_SETTINGS['ACCOUNTS']

RECEIPTS_CREATE = 'receipts.create'
RECEIPTS_PAY = 'receipts.pay'
RECEIPTS_SEND = 'receipts.send'
RECEIPTS_GET = 'receipts.get'
CARDS_CREATE = 'cards.create'
CARDS_CHECK = 'cards.check'
CARDS_REMOVE = 'cards.remove'
CARDS_GET_VERIFY_CODE = 'cards.get_verify_code'
CARD_VERIFY = 'cards.verify'

TEST_URL = 'https://checkout.test.paycom.uz/api'
PRODUCTION_URL = 'https://checkout.paycom.uz/api'
INITIALIZATION_URL = 'https://checkout.paycom.uz'
TEST_INITIALIZATION_URL = 'https://checkout.test.paycom.uz'
URL = PRODUCTION_URL if TEST_ENV else TEST_URL
LINK = INITIALIZATION_URL if TEST_ENV else TEST_INITIALIZATION_URL

METHOD_CHECK_PERFORM_TRANSACTION = 'CheckPerformTransaction'
METHOD_CREATE_TRANSACTION = 'CreateTransaction'
METHOD_CHECK_TRANSACTION = 'CheckTransaction'
METHOD_PERFORM_TRANSACTION = 'PerformTransaction'
METHOD_CANCEL_TRANSACTION = 'CancelTransaction'
