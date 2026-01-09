from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from config.responses import ResponseSuccess, ResponseFail
from shop.models import Medicine
from specialist.models import Doctor
from .models import CommentDoctor, CommentMedicine
from .serializers import CommentDoctorSerializer, CommentMedicineSerializer, CommentPostSerializer, QuestionSerializer


class CommentDoctorView(APIView):
    # queryset = NewsModel.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = CommentDoctorSerializer


    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        responses={
            '200': CommentDoctorSerializer()
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="test manual param",
                              type=openapi.TYPE_NUMBER)
        ], operation_description='GET News')
    @action(detail=False, methods=['get'])
    def get(self, request):
        key = request.GET.get('pk', False)
        if key:
            comment = CommentDoctor.objects.filter(doctor_id=key)
            serializer = CommentDoctorSerializer(comment, many=True)
            return ResponseSuccess(data=serializer.data, request=request.method)

    @swagger_auto_schema(
        operation_id='rate_doctor',
        operation_description="rate_doctor",
        request_body=CommentPostSerializer(),
        responses={
            '200': CommentDoctorSerializer()
        },
    )
    def post(self, request):
        doctor = Doctor.objects.get(id=request.data['pk'])
        serializer = CommentDoctorSerializer(data=request.data)
        if serializer.is_valid():
            comment = CommentDoctor()
            comment.text = request.data['text']
            comment.rate = request.data['rate']
            comment.user = request.user
            comment.doctor = doctor
            comment.save()
            s = CommentDoctorSerializer(comment)
            return ResponseSuccess(data=s.data, request=request.method)
        return ResponseFail(data=serializer.errors, request=request.method)


class CommentMedicineView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        # request_body=DoctorSerializer(),
        responses={
            '200': CommentMedicineSerializer()
        },
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_QUERY, description="test manual param",
                              type=openapi.TYPE_NUMBER)
        ], operation_description='GET News')
    @action(detail=False, methods=['get'])
    def get(self, request):
        key = request.GET.get('pk', False)
        if key:
            comment = CommentMedicine.objects.filter(medicine_id=key)
            serializer = CommentMedicineSerializer(comment, many=True)
            return ResponseSuccess(data=serializer.data, request=request.method)

    @swagger_auto_schema(
        operation_id='rate_medicines',
        operation_description="rate_medicines",
        request_body=CommentPostSerializer(),
        responses={
            '200': CommentMedicineSerializer()
        },
    )
    def post(self, request):
        medicine = Medicine.objects.get(id=request.data['pk'])
        serializer = CommentMedicineSerializer(data=request.data)
        if serializer.is_valid():
            comment = CommentMedicine(**serializer.data)
            comment.user = request.user
            comment.rate = request.data['rate']
            comment.medicine = medicine
            comment.save()
            s = CommentMedicineSerializer(comment)
            return ResponseSuccess(data=s.data, request=request.method)
        return ResponseFail(data=serializer.errors, request=request.method)


class QuestionView(APIView):
    @swagger_auto_schema(
        operation_id='question',
        operation_description="Send Question",
        request_body=QuestionSerializer(),
    )
    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseSuccess(data='Success')
        else:
            return ResponseFail(data=serializer.errors)
