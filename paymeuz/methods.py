import requests

from shop.models import CartModel, Medicine, OrderModel
from .keywords import *
import base64
import random

rand_id = random.randint(100, 999)


def create_cards(card_number, expire, save=False) -> dict:
    data = dict(
        method=CARDS_CREATE,
        params=dict(
            card=dict(number=card_number, expire=expire),
            save=save
        )
    )
    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION)
    result = response.json()
    if 'error' in result:
        return result

    # token = result['result']['card']['token']
    # result = cards_get_verify_code(token=token)
    return result


def cards_get_verify_code(token) -> dict:
    data = dict(
        method=CARDS_GET_VERIFY_CODE,
        params=dict(token=token)
    )
    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION)
    result = response.json()
    # result.update(token=token)

    return result


def cards_verify(code, token):
    data = dict(
        method=CARD_VERIFY,
        params=dict(
            token=token,
            code=code
        )
    )
    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION)
    return response.json()


def cards_check(token):
    data = dict(
        method=CARDS_CHECK,
        params=dict(
            token=token,
        )
    )
    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION)
    return response.json()


def cards_remove(token):
    data = dict(
        method=CARDS_REMOVE,
        params=dict(
            token=token,
        )
    )
    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION)
    return response.json()


def create_transaction(full_name, product_name, order_id, amount, order_type=None) -> dict:
    try:
        order = OrderModel.objects.get(id=order_id, payment_status=1)
    except:
        return dict(error = "order not found")

    items = []

    for cart in order.cart_products:
        medicine: Medicine = cart.product
        items_detail = dict()

        items_detail['title'] = medicine.title
        items_detail['price'] = medicine.cost * 100
        items_detail['count'] = cart.amount
        items_detail['vat_percent'] = 12

        # IKPU / Package Code
        items_detail['code'] = medicine.product_ikpu
        items_detail['package_code'] = medicine.product_package_code

        items.append(items_detail)

    data = dict(
        method=RECEIPTS_CREATE,
        params=dict(
            amount=amount * 100,
            account={
                "full_name": full_name,
                "product_name": product_name,
                "order_id": order_id
            },
            detail={
                "receipt_type": 0,
                "items": items
            }
        )
    )

    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION_TRANSACTION)
    result = response.json()

    return result


def pay_transaction(pk, token) -> dict:
    data = dict(
        method=RECEIPTS_PAY,
        params=dict(
            id=pk,
            token=token
        )  # 900513533 abduhamid
    )

    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION_TRANSACTION)
    result = response.json()
    return result


def send_transaction(pk, phone) -> dict:
    data = dict(
        method=RECEIPTS_SEND,
        params=dict(
            id=pk,
            phone=phone
        )
    )

    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION_TRANSACTION)
    result = response.json()

    return result


def get_transaction(pk) -> dict:
    data = dict(
        method=RECEIPTS_GET,
        params=dict(
            id=pk,
        )
    )
    response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION_TRANSACTION)
    result = response.json()

    return result


def send_order(order_id) -> dict:
    order = OrderModel.objects.get(id=order_id)
    products = CartModel.objects.filter(user=order.user, status=1)

    message = f"Order #{order.id}\n"
    message += f"<b>Mijoz</b>: {order.user.get_full_name()}\n"
    message += f"<b>Telefon raqam</b>: +{order.user.username}\n\n"

    message += f"<b>Buyurtmalar</b>: \n"
    for product in products:
        message += f"- {product.product.name} x{product.amount} dona\n"

    message += f"\n<b>Umumiy summa</b>: {order.price} so'm"
    message += f"\n<b>To'lov turi</b>: "

    if order.payment_type == 1:
        message += "Naqd\n"
    elif order.payment_type == 2:
        message += "Plastik karta\n"
    elif order.payment_type == 3:
        message += "Bank orqali\n"

    if order.shipping_address is None:
        message += "<b>Manzil</b>: kiritilmagan"
    else:
        shipping_address = order.shipping_address
        address = f"{shipping_address.region}, {shipping_address.full_address}"
        message += f"<b>Manzil</b>: {address}\n"

        if shipping_address.apartment_office is not None:
            message += f", {shipping_address.apartment_office}"

        if shipping_address.floor is not None:
            message += f" {shipping_address.floor}-qavat"

        if shipping_address.door_or_phone is not None:
            message += f", {shipping_address.door_or_phone}"

        if shipping_address.instructions is not None:
            message += f"\n<i>Qo'shimcha ma'lumot</i>: {shipping_address.instructions}"

    data = dict({
        "chat_id": TELEGRAM_ORDERS_GROUP_ID,
        "parse_mode": "HTML",
        "text": message
    })

    response = requests.post(url=TELEGRAM_PAYLOAD_URL + "/sendMessage", json=data)
    result = response.json()

    return result


class Paymeuz:

    def create_transaction(self, token, order_id, amount, order_type=None) -> dict:
        data = dict(
            method=RECEIPTS_CREATE,
            params=dict(
                amount=amount * 100,
                account={
                    KEY_1: order_id,
                    KEY_2: order_type
                }
            )
        )
        response = requests.post(
            url=PRODUCTION_URL,
            json=data,
            headers=AUTHORIZATION
        )
        result = response.json()

        if 'error' in result:
            print('errrror')
            return result
        print(result['result']['receipt']['_id'])
        data = dict(
            method=RECEIPTS_PAY,
            params=dict(
                id=result['result']['receipt']['_id'],
                token=token
            )
        )

        response = requests.post(url=PRODUCTION_URL, json=data, headers=AUTHORIZATION)
        print('asd')
        return response.json()

    def create_cards(self, card_number, expire, amount, save=False) -> dict:
        data = dict(
            method=CARDS_CREATE,
            params=dict(
                card=dict(number=card_number, expire=expire),
                amount=amount,
                save=save
            )
        )

        response = requests.post(url=URL, json=data, headers=AUTHORIZATION)
        result = response.json()
        if 'error' in result:
            return result

        token = result['result']['card']['token']
        result = self.cards_get_verify_code(token=token)
        return result

    def cards_get_verify_code(self, token) -> dict:
        data = dict(
            method=CARDS_GET_VERIFY_CODE,
            params=dict(token=token)
        )
        response = requests.post(url=URL, json=data, headers=AUTHORIZATION)
        result = response.json()
        result.update(token=token)

        return result

    def cards_verify(self, code, token):
        data = dict(
            method=CARD_VERIFY,
            params=dict(
                token=token,
                code=code
            )
        )

        response = requests.post(url=URL, json=data, headers=AUTHORIZATION)
        return response.json()

    @staticmethod
    def create_initialization(amount, order_id, return_url, order_type=None):
        params = f"m={TOKEN};ac.{KEY_1}={order_id};a={amount};c={return_url}"
        if order_type:
            params += f"ac.{KEY_2}"
        encode_params = base64.b64encode(params.encode("utf-8"))
        encode_params = str(encode_params, 'utf-8')
        url = f"{LINK}/{encode_params}"
        return url

    def check_order(self, amount, account):
        raise NotImplemented
