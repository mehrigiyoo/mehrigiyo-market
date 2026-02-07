import base64
import json
from datetime import timezone

from django.conf import settings


class PaymeService:
    """Payme Merchant API Service"""

    PAYME_CONFIG = settings.PAYME_SETTINGS

    # Payme states
    STATE_CREATED = 1
    STATE_COMPLETED = 2
    STATE_CANCELLED = -1
    STATE_CANCELLED_AFTER_COMPLETE = -2

    # Error codes
    ERROR_INVALID_AMOUNT = -31001
    ERROR_INVALID_ACCOUNT = -31050
    ERROR_COULD_NOT_PERFORM = -31008
    ERROR_TRANSACTION_NOT_FOUND = -31003
    ERROR_CANT_CANCEL = -31007

    @classmethod
    def check_auth(cls, request):
        """
        Verify Payme authentication

        Payme sends: Authorization: Basic base64(merchant_id:password)
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Basic '):
            return False

        try:
            # Decode base64
            encoded = auth_header.split('Basic ')[1]
            decoded = base64.b64decode(encoded).decode('utf-8')

            # Expected format: merchant_id:password
            merchant_id, password = decoded.split(':')

            # Verify
            expected_merchant = cls.PAYME_CONFIG['MERCHANT_ID']
            expected_password = cls.PAYME_CONFIG['SECRET_KEY']

            return (merchant_id == expected_merchant and
                    password == expected_password)

        except Exception:
            return False

    @classmethod
    def create_checkout_url(cls, payment):
        """
        Create Payme checkout URL

        Returns: URL client should be redirected to
        """
        merchant_id = cls.PAYME_CONFIG['MERCHANT_ID']

        # Amount in tiyin (1 UZS = 100 tiyin)
        amount_tiyin = int(payment.amount * 100)

        # Account parameter (payment ID)
        account = {
            'order_id': str(payment.id)
        }

        # Encode account to base64
        account_json = json.dumps(account)
        account_base64 = base64.b64encode(account_json.encode()).decode()

        # Callback URL
        callback = settings.PAYME_CALLBACK_URL

        # Build URL
        env = cls.PAYME_CONFIG['ENVIRONMENT']
        base_url = cls.PAYME_CONFIG['ENDPOINT'][env]

        checkout_url = (
            f"{base_url}/{merchant_id}"
            f"?amount={amount_tiyin}"
            f"&account={account_base64}"
            f"&callback={callback}"
        )

        return checkout_url

    @classmethod
    def check_perform_transaction(cls, params):
        """
        CheckPerformTransaction method

        Payme asks: Can this payment be performed?
        """
        account = params.get('account', {})
        amount = params.get('amount')  # in tiyin

        order_id = account.get('order_id')

        # Find payment
        from paymeuz.models import Payment

        try:
            payment = Payment.objects.get(id=order_id)
        except Payment.DoesNotExist:
            return {
                'error': {
                    'code': cls.ERROR_INVALID_ACCOUNT,
                    'message': 'Payment not found'
                }
            }

        # Check amount
        expected_amount = int(payment.amount * 100)
        if amount != expected_amount:
            return {
                'error': {
                    'code': cls.ERROR_INVALID_AMOUNT,
                    'message': f'Invalid amount. Expected: {expected_amount}'
                }
            }

        # Check if payment already paid
        if payment.status == 'paid':
            return {
                'error': {
                    'code': cls.ERROR_COULD_NOT_PERFORM,
                    'message': 'Payment already completed'
                }
            }

        # Success
        return {
            'result': {
                'allow': True
            }
        }

    @classmethod
    def create_transaction(cls, params):
        """
        CreateTransaction method

        Payme creates transaction on their side
        """
        transaction_id = params.get('id')
        account = params.get('account', {})
        amount = params.get('amount')
        time = params.get('time')

        order_id = account.get('order_id')

        from paymeuz.models import Payment, PaymentTransaction

        try:
            payment = Payment.objects.get(id=order_id)
        except Payment.DoesNotExist:
            return {
                'error': {
                    'code': cls.ERROR_INVALID_ACCOUNT,
                    'message': 'Payment not found'
                }
            }

        # Check if transaction already exists
        existing = PaymentTransaction.objects.filter(
            transaction_id=transaction_id
        ).first()

        if existing:
            # Return existing transaction
            return {
                'result': {
                    'create_time': existing.created_at.timestamp() * 1000,
                    'transaction': str(existing.id),
                    'state': existing.state or cls.STATE_CREATED
                }
            }

        # Create new transaction
        transaction = PaymentTransaction.objects.create(
            payment=payment,
            transaction_id=transaction_id,
            method='CreateTransaction',
            request_data=params,
            state=cls.STATE_CREATED
        )

        # Update payment
        payment.payme_transaction_id = transaction_id
        payment.payme_time = time
        payment.payme_state = cls.STATE_CREATED
        payment.status = 'processing'
        payment.save()

        return {
            'result': {
                'create_time': int(transaction.created_at.timestamp() * 1000),
                'transaction': str(transaction.id),
                'state': cls.STATE_CREATED
            }
        }

    @classmethod
    def perform_transaction(cls, params):
        """
        PerformTransaction method

        Actually perform the payment
        """
        transaction_id = params.get('id')

        from paymeuz.models import PaymentTransaction

        try:
            transaction = PaymentTransaction.objects.get(
                transaction_id=transaction_id
            )
        except PaymentTransaction.DoesNotExist:
            return {
                'error': {
                    'code': cls.ERROR_TRANSACTION_NOT_FOUND,
                    'message': 'Transaction not found'
                }
            }

        payment = transaction.payment

        # Check state
        if transaction.state == cls.STATE_COMPLETED:
            # Already completed
            return {
                'result': {
                    'transaction': str(transaction.id),
                    'perform_time': int(payment.paid_at.timestamp() * 1000),
                    'state': cls.STATE_COMPLETED
                }
            }

        # Complete transaction
        from django.utils import timezone

        transaction.state = cls.STATE_COMPLETED
        transaction.save()

        payment.payme_state = cls.STATE_COMPLETED
        payment.mark_as_paid(transaction_id)

        perform_time = int(timezone.now().timestamp() * 1000)

        return {
            'result': {
                'transaction': str(transaction.id),
                'perform_time': perform_time,
                'state': cls.STATE_COMPLETED
            }
        }

    @classmethod
    def check_transaction(cls, params):
        """
        CheckTransaction method

        Check transaction status
        """
        transaction_id = params.get('id')

        from paymeuz.models import PaymentTransaction

        try:
            transaction = PaymentTransaction.objects.get(
                transaction_id=transaction_id
            )
        except PaymentTransaction.DoesNotExist:
            return {
                'error': {
                    'code': cls.ERROR_TRANSACTION_NOT_FOUND,
                    'message': 'Transaction not found'
                }
            }

        payment = transaction.payment

        result = {
            'create_time': int(transaction.created_at.timestamp() * 1000),
            'transaction': str(transaction.id),
            'state': transaction.state or cls.STATE_CREATED,
        }

        if transaction.state == cls.STATE_COMPLETED and payment.paid_at:
            result['perform_time'] = int(payment.paid_at.timestamp() * 1000)

        if transaction.state in [cls.STATE_CANCELLED, cls.STATE_CANCELLED_AFTER_COMPLETE]:
            result['cancel_time'] = int((payment.cancelled_at or timezone.now()).timestamp() * 1000)
            result['reason'] = transaction.reason or 0

        return {'result': result}

    @classmethod
    def cancel_transaction(cls, params):
        """
        CancelTransaction method

        Cancel transaction
        """
        transaction_id = params.get('id')
        reason = params.get('reason')

        from paymeuz.models import PaymentTransaction
        from django.utils import timezone

        try:
            transaction = PaymentTransaction.objects.get(
                transaction_id=transaction_id
            )
        except PaymentTransaction.DoesNotExist:
            return {
                'error': {
                    'code': cls.ERROR_TRANSACTION_NOT_FOUND,
                    'message': 'Transaction not found'
                }
            }

        payment = transaction.payment

        # Determine new state
        if transaction.state == cls.STATE_CREATED:
            new_state = cls.STATE_CANCELLED
        elif transaction.state == cls.STATE_COMPLETED:
            new_state = cls.STATE_CANCELLED_AFTER_COMPLETE
        else:
            # Already cancelled
            return {
                'result': {
                    'transaction': str(transaction.id),
                    'cancel_time': int((payment.cancelled_at or timezone.now()).timestamp() * 1000),
                    'state': transaction.state
                }
            }

        # Cancel
        transaction.state = new_state
        transaction.reason = reason
        transaction.save()

        payment.payme_state = new_state
        payment.payme_reason = reason
        payment.cancel(f"Payme cancellation. Reason: {reason}")

        cancel_time = int(timezone.now().timestamp() * 1000)

        return {
            'result': {
                'transaction': str(transaction.id),
                'cancel_time': cancel_time,
                'state': new_state
            }
        }