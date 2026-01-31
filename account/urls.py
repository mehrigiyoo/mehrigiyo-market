from django.db import router
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

from .views import (SendSmsView, ConfirmSmsView, ChangePassword, UserAvatarUpdateView, PhoneCheckAPI, RegionView,
                    CountryView, ResetPasswordAPIView, LogoutAPIView, DeleteAccountAPIView, UserDeviceViewSet)


# Router yaratish
router = DefaultRouter()
router.register(r'devices', UserDeviceViewSet, basename='device')


urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/logout/', LogoutAPIView.as_view(), name='auth-logout'),
    path('profile/delete/', DeleteAccountAPIView.as_view(), name='account-delete'),
    path('phone-check/', PhoneCheckAPI.as_view(), name='phone-check'),
    path('send/sms/', SendSmsView.as_view()),
    path('send/sms/confirm/', ConfirmSmsView.as_view()),
    path('change/password/', ChangePassword.as_view()),
    path('reset/password/', ResetPasswordAPIView.as_view()),
    path('avatar/update/', UserAvatarUpdateView.as_view()),
    path('country/', CountryView.as_view()),
    path('region/', RegionView.as_view()),

    path('', include(router.urls)),
    # path('add/address/', AddAddressView.as_view()),
    # path('for-admin-user/', UserForAdminViewAPI.as_view()),
    # path('for-admin-referal-user/', ReferalUserForAdminViewAPI.as_view()),
    # path('deliver/address/', DeliverAddressView.as_view()),
    # path('offer/', OfferView.as_view()),
    # path('set/registrationkey/', SetRegistrationKeyView.as_view()),
    #
    # path('set/notification_key/', SetNotificationKeyView.as_view()),
]
