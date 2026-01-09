from django.urls import path
from .merchant_views import PaymeCallbackView
from .views import CardView, PayTransactionView, CardGetVerifyCodeView, UserReferralView

urlpatterns = [
    # path('click/transaction/', ClickCallbackView.as_view()),
    # path('payme/transaction/', PaymeCallbackView.as_view()),
    path('card/', CardView.as_view()),
    path('card/verify/', CardGetVerifyCodeView.as_view()),
    # path('card/remove/<int:pk>/', CardRemoveView.as_view()),
    path('pay/', PayTransactionView.as_view()),
    path('user-referral/', UserReferralView.as_view(), name='user-referral'),
]
