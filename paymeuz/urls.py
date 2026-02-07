# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
#
# from .views import PaymentViewSet
# from .payme.views import PaymeCallbackView
#
# # Router for REST API
# router = DefaultRouter()
# router.register(r'payments', PaymentViewSet, basename='payment')
#
urlpatterns = [
#     # REST API
#     path('', include(router.urls)),
#
#     # Payme callback (Merchant API)
#     path('payments/payme/callback/', PaymeCallbackView.as_view(), name='payme-callback'),
]