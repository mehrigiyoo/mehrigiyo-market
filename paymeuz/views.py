# # ============================================
# # FILE: payment/views.py - UPDATE
# # ============================================
#
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.contrib.contenttypes.models import ContentType
#
# from .models import Payment
# from .serializers import PaymentSerializer
# from .payme.service import PaymeService
#
#
# class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     Payment management (client view)
#
#     Endpoints:
#     - GET  /api/payments/          - List my payments
#     - GET  /api/payments/{id}/     - Get payment detail
#     - POST /api/payments/create/   - Create payment
#     - GET  /api/payments/{id}/status/ - Check status
#     """
#
#     permission_classes = [IsAuthenticated]
#     serializer_class = PaymentSerializer
#
#     def get_queryset(self):
#         """Get user's payments"""
#         return Payment.objects.filter(user=self.request.user)
#
#     @action(detail=False, methods=['post'])
#     def create(self, request):
#         """
#         Create payment
#
#         POST /api/payments/create/
#         {
#             "payment_type": "market",     # or "consultation"
#             "object_id": 123,             # Order ID or Consultation ID
#             "payment_method": "payme"
#         }
#
#         Response:
#         {
#             "payment_id": "uuid...",
#             "payment_url": "https://checkout.paycom.uz/...",
#             "amount": 150000,
#             "payment_type": "market"
#         }
#         """
#         payment_type = request.data.get('payment_type')
#         object_id = request.data.get('object_id')
#         payment_method = request.data.get('payment_method', 'payme')
#
#         # Validate payment type
#         if payment_type not in ['market', 'consultation']:
#             return Response(
#                 {'error': 'Invalid payment_type. Must be "market" or "consultation"'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Get model based on type
#         if payment_type == 'market':
#             from order.models import Order
#             model = Order
#         else:  # consultation
#             from consultation.models import ConsultationRequest
#             model = ConsultationRequest
#
#         # Get object
#         try:
#             obj = model.objects.get(id=object_id, customer=request.user)
#         except model.DoesNotExist:
#             return Response(
#                 {'error': 'Object not found or access denied'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#
#         # Check if already paid
#         existing_payment = Payment.objects.filter(
#             content_type=ContentType.objects.get_for_model(model),
#             object_id=object_id,
#             status='paid'
#         ).first()
#
#         if existing_payment:
#             return Response(
#                 {'error': 'Already paid'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Create payment
#         content_type = ContentType.objects.get_for_model(model)
#
#         # Get amount
#         if payment_type == 'market':
#             amount = obj.total_amount
#             description = f"Order #{obj.order_number}"
#         else:
#             amount = obj.doctor.consultation_price
#             description = f"Consultation with Dr. {obj.doctor.first_name}"
#
#         payment = Payment.objects.create(
#             user=request.user,
#             payment_type=payment_type,
#             content_type=content_type,
#             object_id=object_id,
#             amount=amount,
#             payment_method=payment_method,
#             description=description,
#             ip_address=self.get_client_ip(request),
#             user_agent=request.META.get('HTTP_USER_AGENT', ''),
#             metadata={
#                 'object_type': payment_type,
#                 'object_id': object_id,
#             }
#         )
#
#         # Generate payment URL
#         if payment_method == 'payme':
#             payment_url = PaymeService.create_checkout_url(payment)
#         else:
#             return Response(
#                 {'error': 'Unsupported payment method'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         return Response({
#             'payment_id': str(payment.id),
#             'payment_url': payment_url,
#             'amount': float(payment.amount),
#             'payment_type': payment_type,
#             'description': description,
#         }, status=status.HTTP_201_CREATED)
#
#     @action(detail=True, methods=['get'])
#     def status(self, request, pk=None):
#         """
#         Check payment status
#
#         GET /api/payments/{id}/status/
#
#         Response:
#         {
#             "payment_id": "uuid...",
#             "status": "paid",
#             "amount": 150000,
#             "paid_at": "2024-10-01T10:00:00Z"
#         }
#         """
#         payment = self.get_object()
#
#         return Response({
#             'payment_id': str(payment.id),
#             'status': payment.status,
#             'payment_type': payment.payment_type,
#             'amount': float(payment.amount),
#             'created_at': payment.created_at,
#             'paid_at': payment.paid_at,
#         })
#
#     def get_client_ip(self, request):
#         """Get client IP address"""
#         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             ip = x_forwarded_for.split(',')[0]
#         else:
#             ip = request.META.get('REMOTE_ADDR')
#         return ip