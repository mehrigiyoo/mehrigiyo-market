from django.urls import path, include
from rest_framework import routers
from .views import (UserModelAdminViewSet, SmsCodeAdminViewSet, SmsAttemptAdminViewSet, CountyModelAdminViewSet,
                    RegionModelAdminViewSet, DeliveryAddressAdminViewSet, MessageAdminViewSet, ChatRoomAdminViewSet,
                    CommentDoctorAdminViewSet, CommentMedicineAdminViewSet, NewsModelAdminViewSet,
                    PaymeTransactionModelAdminViewSet, CardAdminViewSet, PicturesMedicineAdminViewSet,
                    TypeMedicineAdminViewSet, MedicineAdminViewSet, CartModelAdminViewSet, DeliveryManAdminViewSet,
                    OrderModelAdminViewSet, TypeDoctorAdminViewSet, DoctorAdminViewSet, RateDoctorAdminViewSet,
                    AdviceTimeAdminViewSet, NotificationAdminViewSet)
router = routers.DefaultRouter()

# router.register(r'User', UserModelAdminViewSet)
# router.register(r'SmsCode', SmsCodeAdminViewSet)
# router.register(r'SmsAttempt', SmsAttemptAdminViewSet)
# router.register(r'CountyModel', CountyModelAdminViewSet)
# router.register(r'RegionModel', RegionModelAdminViewSet)
# router.register(r'DeliveryAddress', DeliveryAddressAdminViewSet)
# router.register(r'Message', MessageAdminViewSet)
# router.register(r'ChatRoom', ChatRoomAdminViewSet)
# router.register(r'CommentDoctor', CommentDoctorAdminViewSet)
# router.register(r'CommentMedicine', CommentMedicineAdminViewSet)
# router.register(r'NewsModel', NewsModelAdminViewSet)
# router.register(r'Notification', NotificationAdminViewSet)
# router.register(r'PaymeTransaction', PaymeTransactionModelAdminViewSet)
# router.register(r'Card', CardAdminViewSet)
# router.register(r'PicturesMedicine', PicturesMedicineAdminViewSet)
# router.register(r'TypeMedicine', TypeMedicineAdminViewSet)
# router.register(r'Medicine', MedicineAdminViewSet)
# router.register(r'Cart', CartModelAdminViewSet)
# router.register(r'DeliveryMan', DeliveryManAdminViewSet)
# router.register(r'OrderModel', OrderModelAdminViewSet)
# router.register(r'TypeDoctor', TypeDoctorAdminViewSet)
# router.register(r'Doctor', DoctorAdminViewSet)
# router.register(r'RateDoctor', RateDoctorAdminViewSet)
# router.register(r'AdviceTime', AdviceTimeAdminViewSet)


urlpatterns = [
    # path('', include(router.urls)),
]
