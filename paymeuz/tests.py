# from django.test import TestCase
# from django.contrib.auth import get_user_model
# from .models import Payment
# from .payme.service import PaymeService
#
# User = get_user_model()
#
#
# class PaymeServiceTest(TestCase):
#
#     def setUp(self):
#         self.user = User.objects.create(
#             phone='998901234567',
#             role='client'
#         )
#
#     def test_create_checkout_url(self):
#         """Test Payme checkout URL generation"""
#         payment = Payment.objects.create(
#             user=self.user,
#             payment_type='market',
#             amount=100000,
#             payment_method='payme'
#         )
#
#         url = PaymeService.create_checkout_url(payment)
#
#         self.assertIn('checkout.paycom.uz', url)
#         self.assertIn(str(payment.id), url)
#
#     def test_check_perform_transaction(self):
#         """Test CheckPerformTransaction"""
#         payment = Payment.objects.create(
#             user=self.user,
#             payment_type='consultation',
#             amount=50000,
#             payment_method='payme'
#         )
#
#         params = {
#             'account': {'order_id': str(payment.id)},
#             'amount': 5000000  # 50000 * 100 (tiyin)
#         }
#
#         result = PaymeService.check_perform_transaction(params)
#
#         self.assertIn('result', result)
#         self.assertTrue(result['result']['allow'])