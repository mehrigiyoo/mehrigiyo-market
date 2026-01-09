from rest_framework.views import APIView

from config.models import ConfigModel
from config.responses import ResponseFail, ResponseSuccess

class VersionView(APIView):
    def get(self, request):
        queryset = ConfigModel.objects.first()
        version = request.GET.get('version')

        if version is None:
            return ResponseFail(data="Version parameter not found!")

        if queryset is None:
            return ResponseFail(data="Version is not set!")

        if queryset.version != version:
            return ResponseFail(data=False)

        return ResponseSuccess(data=True)

    def post(self, request):
        queryset = ConfigModel.objects.first()
        version = request.data['version']

        if queryset is None:
            ConfigModel.objects.create(
                version=version
            )

            return ResponseSuccess(data="Created")

        queryset.version = version
        queryset.save()

        return ResponseSuccess(data="Updated")
