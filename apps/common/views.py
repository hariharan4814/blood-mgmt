from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers


class HealthCheckView(APIView):
    """
    Simple API health check endpoint to verify backend status.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Health Check",
        description="Verify backend server availability and health status.",
        responses={
            200: inline_serializer(
                name="HealthCheckResponse",
                fields={
                    "status": serializers.CharField(),
                    "message": serializers.CharField(),
                },
            )
        },
        tags=["System"]
    )
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "message": "Blood Management System API is running"
            },
            status=status.HTTP_200_OK
        )
