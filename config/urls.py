"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from account.views import LoginView

schema_view = get_schema_view(
    openapi.Info(
        title="Mehrigiyo API",
        default_version='v1',
        description="Mehrigiyo - application!",
        terms_of_service="https://www.google.com/policies/terms/",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)



# def home(request):
#     return HttpResponse("Welcome to Imorganic!")


urlpatterns = [
    # path('', home),  # root URL
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('api/', include([
        path('auth/login/', LoginView.as_view(), name='auth-login'),
        path('user/', include('account.urls')),
        path('news/', include('news.urls')),
        path('comment/', include('comment.urls')),
        path('shop/', include('shop.urls')),
        path('payme/', include('paymeuz.urls')),

        # path('notifications/', ),
        # path('notification/send/', SendNotificationView.as_view()),

        path('specialist/', include('specialist.urls')),
        path('call/', include('call.urls')),  # Call API
        path('chat/', include('chat.urls')),
        path('client/', include('client.urls')),
        path('support/', include('support.urls')),
        path('admin/', include('api.urls')),

        # path('config/', include([
        #     path('version/', VersionView.as_view())
        # ]))
    ]))
]
urlpatterns += i18n_patterns(

)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
