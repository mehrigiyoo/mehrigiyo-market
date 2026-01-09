from rest_framework.response import Response
from rest_framework import status


class ResponseFail(Response):
    def __init__(self, data="", request=""):
        data = {"status": "fail", "data": data, "request": request}
        super().__init__(data, status=status.HTTP_200_OK)


class ResponseSuccess(Response):
    def __init__(self, data="", request=""):
        if isinstance(data, Response):
            data = data.data

        data = {"status": "success", "data": data, "request": request}
        super().__init__(data, status=status.HTTP_200_OK)

