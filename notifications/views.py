from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.responses import ResponseSuccess, ResponseFail
from config.settings import FIREBASE_REGISTRATION_KEYS
from account.models import UserModel
from django.db.models.manager import BaseManager

class NewsView(generics.ListAPIView):
    pass
