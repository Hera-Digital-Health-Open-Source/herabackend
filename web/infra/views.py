from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[],
        request=None,
        responses=None,
    )
    def get(self, request: Request) -> Response:
        return Response(
            status=200,
        )
