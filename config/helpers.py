import requests
import time
from django.conf import settings
import random

from django.utils import timezone

from account.models import SmsCode
from datetime import timedelta
from django.core.exceptions import SuspiciousOperation


def generate_sms_code():
    return str(random.randint(100000, 999999))


def send_sms_code(request, phone, purpose):
    # IP aniqlash
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    # Oldingi aktiv kodlarni o‘ldiramiz (MUHIM)
    SmsCode.objects.filter(
        phone=phone,
        purpose=purpose,
        confirmed=False,
        expire_at__gte=timezone.now()
    ).update(expire_at=timezone.now())

    # Rate limit (basic)
    if SmsCode.objects.filter(phone=phone).count() > 1000:
        raise SuspiciousOperation("SMS limit exceeded")

    # Kod yaratamiz
    code = generate_sms_code()

    SmsCode.objects.create(
        phone=phone,
        ip=ip,
        code=code,
        purpose=purpose,
        expire_at=timezone.now() + timedelta(minutes=5),
        confirmed=False
    )

    # SMS matni
    if purpose == 'activate':
        message = f"Doctor Ali ilovasi uchun tasdiqlash kodi: {code}"
    elif purpose == 'reset_password':
        message = f"Parolni tiklash kodi: {code}"
    else:
        message = f"Tasdiqlash kodi: {code}"

    # Eskizga yuboramiz
    send_sms_eskiz(phone, message)

    return code

# def sms_code():
#     return str(random.randint(100000, 999999))


# def send_sms_code(request, phone, send_link, signature):
#     active_codes = SmsCode.objects.filter(phone=phone, confirmed=False)
#     if active_codes.count() >= 3:
#         active_codes.earliest('expire_at').delete()
#
#     if send_link:
#         send_sms(phone, "link")
#         return 0
#     else:
#         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             ip = x_forwarded_for.split(',')[0]
#         else:
#             ip = request.META.get('REMOTE_ADDR')
#
#         ip_count = SmsCode.objects.filter(ip=ip).count()
#         if ip_count > 1000:
#             raise SuspiciousOperation("Over limit")
#
#         phone_count = SmsCode.objects.filter(phone=phone).count()
#         if phone_count > 1000:
#             raise SuspiciousOperation("Over limit")
#
#         code = sms_code()
#
#         model = SmsCode()
#         model.ip = ip
#         model.phone = phone
#         model.code = code
#         model.expire_at = datetime.now() + timedelta(minutes=10)
#         model.save()
#
#         # verification_message = f"[Doctor Ali] Tasdiqlash kodi: {code}\n{signature}"
#         verification_message_eskiz = f"Doctor Ali ilovasida ro‘yxatdan o‘tish uchun tasdiqlash kodi: {code}"
#
#         # send_sms(phone, verification_message)
#         send_sms_eskiz(phone, verification_message_eskiz)
#         return code


# def validate_sms_code(phone, code):
#     try:
#         obj = SmsAttempt.objects.get(phone=phone)
#         if obj.counter >= 1000:
#             return False
#
#         obj.counter = F('counter') + 1
#     except SmsAttempt.DoesNotExist:
#         obj = SmsAttempt(phone=phone, counter=1)
#
#     obj.last_attempt_at = datetime.now()
#     obj.save()
#
#     codes = SmsCode.objects.filter(phone=phone, expire_at__gt=datetime.now()).all()
#
#     for row in codes:
#         if row.code == code:
#             row.confirmed = True
#             row.save()
#             return True
#
#     return False


ESKIZ_PAYLOAD = 'https://notify.eskiz.uz/api'


def sms_get_auth_token():
    try:
        r = requests.post(f"{ESKIZ_PAYLOAD}/auth/login", json={
            'email': settings.ESKIZ_SMS_USERNAME,
            'password': settings.ESKIZ_SMS_PASSWORD
        })

        data = r.json()
        return data['data']['token']
    except Exception as e:
        print(e)
        return None


def send_sms_eskiz(phone, text):
    auth_token = sms_get_auth_token()
    if auth_token is None:
        print("Error while getting auth token")
        return False

    headers = {
        "Authorization": f"Bearer {auth_token}",
    }

    try:
        r = requests.post(f"{ESKIZ_PAYLOAD}/message/sms/send", json={
            "mobile_phone": phone,
            "message": text,
            "from": "4546"
        }, headers=headers)

        data = r.json()
        print(f"{data['id']} / {data['message']}")

        return True
    except Exception as e:
        print(e)
        return False


def send_sms(phone, text):
    try:
        r = requests.post("http://91.204.239.44/broker-api/send", json={
            'messages': [
                {
                    'recipient': phone,
                    'message-id': 'Mehrigiyo' + str(round(time.time() * 1000)),
                    'sms': {
                        'originator': '3700',
                        'content': {'text': text}
                    }
                }
            ]
        }, auth=(settings.SMS_USERNAME, settings.SMS_PASSWORD))
        print(r.text)
    except Exception as e:
        print(e)
        return False

    return True


def write_req(request):
    f = open('requests.log', 'w+')
    f.write(str(request) + "\n")
    f.close()
