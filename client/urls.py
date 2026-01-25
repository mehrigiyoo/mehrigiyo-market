from django.urls import path
from .views import ClientRegisterView, ClientProfileView, ClientAddressListCreateView, \
    ClientAddressDetailView, ClientAddressBulkDeleteView, MedicineLikeToggleAPIView, FavoriteMedicineListAPIView

urlpatterns = [
    path('register/', ClientRegisterView.as_view(), name='client-register'),
    path('profile/', ClientProfileView.as_view(), name='client-profile'),
    path('addresses/', ClientAddressListCreateView.as_view(), name='client-address-list-create'),
    path('addresses/<int:pk>/', ClientAddressDetailView.as_view(), name='client-address-detail'),
    path('addresses/bulk-delete/', ClientAddressBulkDeleteView.as_view(), name='client-address-bulk-delete'),
    path('medicines/<int:pk>/like/', MedicineLikeToggleAPIView.as_view(), name='medicine-like-toggle'),
    path('medicines/favorites/', FavoriteMedicineListAPIView.as_view(), name='medicine-favorite-list'),


    # path('profile/avatar/update', ClientAvatarUpdateView.as_view()),

]
