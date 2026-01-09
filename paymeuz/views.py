import time
from collections import defaultdict

from django.db.models import Sum
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import UserModel
from account.serializers import UserSerializer
from config.responses import ResponseSuccess, ResponseFail
from shop.models import OrderModel
from .keywords import *
from .methods import (create_cards, cards_get_verify_code, cards_verify, cards_remove, create_transaction,
                      pay_transaction, send_order)
from .models import PaymeTransactionModel, Card
from .serializers import CardSerializer, CardInputSerializer, CardConfirmSerializer, \
    CardSendConfirmSerializer, ReferralSerializer


class CardView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='card',
        operation_description="Card data",
        # request_body=AdvertisingSerializer(),
        responses={
            '200': CardSerializer()
        },
    )
    def get(self, request):
        card = Card.objects.filter(owner=request.user, is_deleted=False)
        serializer = CardSerializer(card, many=True)
        return ResponseSuccess(data=serializer.data, request=request.method)

    @swagger_auto_schema(
        operation_id='create_card',
        operation_description="Create card data",
        request_body=CardInputSerializer(),
        responses={
            '200': CardSerializer()
        },
    )
    def post(self, request):
        serializer = CardInputSerializer(data=request.data)
        if serializer.is_valid():
            data = create_cards(request.data['number'], request.data['expire'], save=True)
            try:
                data = data['result']['card']
            except:
                code = data['error']['code']
                if code == SMS_NOT_CONNECTED:
                    return ResponseFail(data=SMS_NOT_CONNECTED_MESSAGE)
                if code == CARD_NOT_WORKING:
                    return ResponseFail(data=CARD_NOT_WORKING_MESSAGE)
                if code == SYSTEM_ERROR:
                    return ResponseFail(data=SYSTEM_ERROR_MESSAGE)
                return ResponseFail(data=data)
            serializer = CardSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                data = cards_get_verify_code(token=data['token'])
                try:
                    code = data['error']['code']
                    if code == SYSTEM_ERROR:
                        SYSTEM_ERROR_MESSAGE['token'] = data['token']
                        return ResponseFail(data=SYSTEM_ERROR_MESSAGE)
                except:
                    return ResponseSuccess(data=serializer.data)
            else:
                return ResponseFail(data=serializer.errors)

    @swagger_auto_schema(
        operation_id='activate_card',
        operation_description="Activate card data",
        request_body=CardConfirmSerializer(),
        responses={
            '200': CardSerializer()
        },
    )
    def put(self, request):
        card = Card.objects.get(id=request.data['card_id'])
        print(card)
        data = cards_verify(request.data['code'], card.token)
        try:
            data = data['result']['card']
            serializer = CardSerializer(card, data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                # data = cards_check(card.token)
                return ResponseSuccess(data=serializer.data, request=request.method)
        except:
            code = data['error']['code']
            if code == INVALID_CODE:
                return ResponseFail(data=INVALID_CODE_MESSAGE)
            if code == TIME_OUT:
                return ResponseFail(data=TIME_OUT_MESSAGE)
            return ResponseFail(data=data)

    @swagger_auto_schema(
        operation_id='remove_card',
        operation_description="Activate card data",
        request_body=CardSendConfirmSerializer(),
        # responses={
        #     '200': CardSerializer()
        # },
    )
    def delete(self, request):
        card = Card.objects.get(id=request.data['card_id'])
        data = cards_remove(card.token)
        if data:
            card.is_deleted = True
            card.save()
            return ResponseSuccess(data=data)
        else:
            return ResponseFail()


class CardGetVerifyCodeView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='send_verify_card',
        operation_description="Send verify card data",
        request_body=CardSendConfirmSerializer(),
        # responses={
        #     '200': CardSerializer()
        # },
    )
    def post(self, request):
        card = Card.objects.get(id=request.data['card_id'])
        data = cards_get_verify_code(token=card.token)
        print(data)
        try:
            code = data['error']['code']
            if code == SYSTEM_ERROR:
                SYSTEM_ERROR_MESSAGE['token'] = data['token']
                return ResponseFail(data=SYSTEM_ERROR_MESSAGE)
        except:
            return ResponseSuccess(data=data)
        data = cards_get_verify_code(token=request.data['token'])
        return ResponseSuccess(data=data)


class PayTransactionView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_id='send_verify_card',
        operation_description="Send verify card data",
        request_body=CardSendConfirmSerializer(),
        # responses={
        #     '200': CardSerializer()
        # },
    )
    def post(self, request):
        order = None
        try:
            order = OrderModel.objects.get(id=request.data['card_id'], payment_status=1)
        except:
            return ResponseFail(data='Order not found')

        user_name = order.user.get_full_name()
        order_name = f"Cart #{order.id}"

        print(f"Username: {user_name}")
        print(f"Order id: {order_name}")

        data = create_transaction(user_name, order_name, order.id, order.price)
        if 'error' in data:
            print('HAVE A ERROR TO CREATE TRANSACTION')
            order.payment_status = 2
            order.save()
            return ResponseFail(data=data)
        create_time = int(time.time() * 1000)

        model = PaymeTransactionModel()
        model.request_id = order.id
        model._id = data['result']['receipt']['_id']
        model.amount = data['result']['receipt']['amount']
        model.order_id = order.id
        model.state = data['result']['receipt']['state']
        model.create_time = create_time
        model.save()

        data = pay_transaction(model._id, order.credit_card.token)
        if 'error' in data:
            print('HAVE A ERROR TO PAY')
            order.payment_status = 2
            order.save()
            return ResponseFail(data=data)

        model._id = data['result']['receipt']['_id']
        model.amount = data['result']['receipt']['amount']
        model.order_id = order.id
        model.state = data['result']['receipt']['state']
        model.status = SUCCESS
        model.create_time = create_time
        model.save()

        order.payment_status = 3
        order.save()

        # data = send_transaction(model._id, request.user.username)
        # if 'error' in data:
        #     print('HAVE A ERROR TO SEND TRANSACTION')
        #     return ResponseFail(data=data)
        send_order(order.id)
        return ResponseSuccess(data=data)


class UserReferralView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        grouped_data = PaymeTransactionModel.objects.values('request_id').annotate(
            total_amount=Sum('amount')
        )

        order_ids_mapping = defaultdict(list)
        for transaction in PaymeTransactionModel.objects.values('request_id', 'order_id'):
            order_ids_mapping[transaction['request_id']].append(transaction['order_id'])

        result = {}
        if grouped_data:
            data = grouped_data[0]
            request_id = data['request_id']
            order_ids = order_ids_mapping[request_id]
            referrals = []
            for referral in order_ids:
                user_data = UserModel.objects.filter(username=referral).values('first_name', 'username')
                if user_data:
                    user_info = user_data[0]
                    referrals.append(user_info)

            result = {
                'total_amount': data['total_amount'],
                'referrals': referrals
            }

        serializer = ReferralSerializer(result)
        return ResponseSuccess(data=serializer.data, request=request.method)
