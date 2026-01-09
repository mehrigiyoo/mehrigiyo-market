from django.urls import path
from .views import (CheckPhoneNumberView, DeleteUserProfileView, OauthRegisterView, SendSmsView, ConfirmSmsView,
                    RegistrationView, CountryView, RegionView, AddAddressView, SetNotificationKeyView,
                    UserView, MedicineView, DoctorView, DeliverAddressView, OfferView, ChangePassword,
                    SetRegistrationKeyView, UserForAdminViewAPI, ReferalUserForAdminViewAPI)

urlpatterns = [
    path('send/sms/', SendSmsView.as_view()),
    path('send/sms/confirm/', ConfirmSmsView.as_view()),
    path('change/password/', ChangePassword.as_view()),
    path('registration/', RegistrationView.as_view()),
    path('check/', CheckPhoneNumberView.as_view()),
    path('country/', CountryView.as_view()),
    path('region/', RegionView.as_view()),
    path('add/address/', AddAddressView.as_view()),
    path('me/', UserView.as_view()),
    path('for-admin-user/', UserForAdminViewAPI.as_view()),
    path('for-admin-referal-user/', ReferalUserForAdminViewAPI.as_view()),
    path('favorite/medicines/', MedicineView.as_view()),
    path('favorite/doctors/', DoctorView.as_view()),
    path('deliver/address/', DeliverAddressView.as_view()),
    path('offer/', OfferView.as_view()),
    path('set/registrationkey/', SetRegistrationKeyView.as_view()),

    path('set/notification_key/', SetNotificationKeyView.as_view()),
    path('delete/', DeleteUserProfileView.as_view()),

    path('oauth/register/', OauthRegisterView.as_view()),
]
