from django.urls import path
from .views import PartnerTokenView, PartnerRefreshTokenView

app_name = 'partner_auth'

urlpatterns = [
    # Partner token olish
    path('token/', PartnerTokenView.as_view(), name='partner-token'),

    # Refresh token
    path('token/refresh/', PartnerRefreshTokenView.as_view(), name='partner-refresh-token'),
]