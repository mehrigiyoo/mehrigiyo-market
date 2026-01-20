from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from .serializers import CustomTokenSerializer
from .views import (CheckPhoneNumberView, SendSmsView, ConfirmSmsView,
                    CountryView, RegionView, AddAddressView, SetNotificationKeyView,
                    UserView, MedicineView, DeliverAddressView, OfferView, ChangePassword,
                    SetRegistrationKeyView, UserForAdminViewAPI, ReferalUserForAdminViewAPI, UserAvatarUpdateView)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(serializer_class=CustomTokenSerializer)),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('send/sms/', SendSmsView.as_view()),
    path('send/sms/confirm/', ConfirmSmsView.as_view()),
    path('change/password/', ChangePassword.as_view()),
    path('avatar/update/', UserAvatarUpdateView.as_view()),
    # path('register/', RegistrationView.as_view()),
    # path('check/', CheckPhoneNumberView.as_view()),
    # path('country/', CountryView.as_view()),
    # path('region/', RegionView.as_view()),
    # path('add/address/', AddAddressView.as_view()),
    # path('me/', UserView.as_view()),
    # path('for-admin-user/', UserForAdminViewAPI.as_view()),
    # path('for-admin-referal-user/', ReferalUserForAdminViewAPI.as_view()),
    # path('favorite/medicines/', MedicineView.as_view()),
    # path('deliver/address/', DeliverAddressView.as_view()),
    # path('offer/', OfferView.as_view()),
    # path('set/registrationkey/', SetRegistrationKeyView.as_view()),
    #
    # path('set/notification_key/', SetNotificationKeyView.as_view()),
]
