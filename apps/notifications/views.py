from django.db import models
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsSuperAdmin
from .models import EmailRecipient, Notification, NotificationType
from .permissions import CanManageEmailRecipients, IsNotificationRecipient
from .serializers import (
    EmailRecipientSerializer,
    EmailStatusSerializer,
    MarkAllReadResponseSerializer,
    NotificationSerializer,
    TestEmailSerializer,
    UnreadCountSerializer,
)
from .services import (
    get_unread_notification_count,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)


@extend_schema_view(
    get=extend_schema(
        tags=["Notifications"],
        summary="List user notifications",
        description="Retrieve a paginated list of in-app notifications belonging to the authenticated user, ordered newest first.",
        parameters=[
            OpenApiParameter(
                name="is_read",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by read status (true or false).",
                required=False,
            ),
            OpenApiParameter(
                name="notification_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by notification category type (e.g. GENERAL, BLOOD_REQUEST, DONATION, CAMP, ELIGIBILITY, INVENTORY).",
                required=False,
            ),
        ],
        responses={200: NotificationSerializer(many=True)},
    )
)
class NotificationListView(generics.ListAPIView):
    """
    List in-app notifications strictly for the authenticated user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user).select_related("recipient")

        is_read_param = self.request.query_params.get("is_read")
        if is_read_param is not None:
            if is_read_param.lower() in ("true", "1"):
                queryset = queryset.filter(is_read=True)
            elif is_read_param.lower() in ("false", "0"):
                queryset = queryset.filter(is_read=False)

        notif_type = self.request.query_params.get("notification_type")
        if notif_type:
            queryset = queryset.filter(notification_type=notif_type.upper())

        return queryset.order_by("-created_at", "-id")


@extend_schema_view(
    get=extend_schema(
        tags=["Notifications"],
        summary="Retrieve notification detail",
        description="Retrieve an individual notification by ID. Users can only access notifications addressed to themselves.",
        responses={200: NotificationSerializer, 404: OpenApiTypes.OBJECT},
    )
)
class NotificationDetailView(generics.RetrieveAPIView):
    """
    Retrieve single notification with object-level recipient ownership checks.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotificationRecipient]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related("recipient")


@extend_schema(
    tags=["Notifications"],
    summary="Mark single notification as read",
    description="Marks the specified notification as read. The authenticated user must be the recipient.",
    request=None,
    responses={200: NotificationSerializer, 404: OpenApiTypes.OBJECT},
)
class NotificationMarkReadView(APIView):
    """
    Action endpoint to mark a specific notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        updated_notification = mark_notification_as_read(notification, request.user)
        serializer = NotificationSerializer(updated_notification)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Notifications"],
    summary="Mark all user notifications as read",
    description="Marks all unread notifications belonging to the authenticated user as read in bulk.",
    request=None,
    responses={200: MarkAllReadResponseSerializer},
)
class NotificationMarkAllReadView(APIView):
    """
    Action endpoint to mark all unread notifications of the requesting user as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        marked_count = mark_all_notifications_as_read(request.user)
        response_data = {
            "marked_count": marked_count,
            "detail": f"Successfully marked {marked_count} notification(s) as read.",
        }
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Notifications"],
    summary="Get unread notification count",
    description="Retrieves the total count of unread in-app notifications for the authenticated user.",
    responses={200: UnreadCountSerializer},
)
class NotificationUnreadCountView(APIView):
    """
    Endpoint returning the unread notification count.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        unread_count = get_unread_notification_count(request.user)
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


# =====================================================================
# Administrative Email Recipient Management Views
# =====================================================================

@extend_schema_view(
    get=extend_schema(
        tags=["Email Recipients"],
        summary="List managed email recipients",
        description="Administrative endpoint to list email recipient distribution entries. Restricted to Super Admin and Blood Bank Admin.",
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by active status.",
                required=False,
            ),
            OpenApiParameter(
                name="recipient_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by recipient role category.",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search by email or name.",
                required=False,
            ),
        ],
        responses={200: EmailRecipientSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Email Recipients"],
        summary="Create managed email recipient",
        description="Administrative endpoint to add a new recipient to the distribution list. Restricted to Super Admin and Blood Bank Admin.",
        request=EmailRecipientSerializer,
        responses={201: EmailRecipientSerializer, 400: OpenApiTypes.OBJECT},
    ),
)
class EmailRecipientListCreateView(generics.ListCreateAPIView):
    """
    List and create managed email recipients for system distributions.
    """
    serializer_class = EmailRecipientSerializer
    permission_classes = [CanManageEmailRecipients]

    def get_queryset(self):
        queryset = EmailRecipient.objects.select_related("user", "created_by").all()

        is_active_param = self.request.query_params.get("is_active")
        if is_active_param is not None:
            if is_active_param.lower() in ("true", "1"):
                queryset = queryset.filter(is_active=True)
            elif is_active_param.lower() in ("false", "0"):
                queryset = queryset.filter(is_active=False)

        recipient_type = self.request.query_params.get("recipient_type")
        if recipient_type:
            queryset = queryset.filter(recipient_type=recipient_type.upper())

        search = self.request.query_params.get("search")
        if search:
            search_clean = search.strip()
            queryset = queryset.filter(
                models.Q(email__icontains=search_clean) | models.Q(name__icontains=search_clean)
            )

        return queryset.order_by("-created_at")


@extend_schema_view(
    get=extend_schema(
        tags=["Email Recipients"],
        summary="Retrieve email recipient",
        description="Retrieve details of a managed email recipient.",
        responses={200: EmailRecipientSerializer, 404: OpenApiTypes.OBJECT},
    ),
    put=extend_schema(
        tags=["Email Recipients"],
        summary="Update email recipient",
        description="Update an existing email recipient record.",
        request=EmailRecipientSerializer,
        responses={200: EmailRecipientSerializer, 400: OpenApiTypes.OBJECT},
    ),
    patch=extend_schema(
        tags=["Email Recipients"],
        summary="Partially update email recipient",
        description="Partially update an existing email recipient record (e.g. toggle is_active).",
        request=EmailRecipientSerializer,
        responses={200: EmailRecipientSerializer, 400: OpenApiTypes.OBJECT},
    ),
    delete=extend_schema(
        tags=["Email Recipients"],
        summary="Delete email recipient",
        description="Remove a recipient from the distribution list.",
        responses={204: None, 404: OpenApiTypes.OBJECT},
    ),
)
class EmailRecipientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or remove a managed email recipient.
    """
    queryset = EmailRecipient.objects.select_related("user", "created_by").all()
    serializer_class = EmailRecipientSerializer
    permission_classes = [CanManageEmailRecipients]


@extend_schema(
    tags=["Email Management"],
    summary="Get SMTP & Email Backend Configuration Status",
    description="Retrieve public SMTP connection status and backend details. Restricted to Super Administrators. Never returns secrets.",
    responses={200: EmailStatusSerializer},
)
class EmailStatusView(APIView):
    """
    Super Admin endpoint to inspect email delivery infrastructure status.
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        from django.conf import settings
        backend_name = getattr(settings, "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend").split(".")[-1]
        host = getattr(settings, "EMAIL_HOST", "smtp.gmail.com")
        port = getattr(settings, "EMAIL_PORT", 587)
        use_tls = getattr(settings, "EMAIL_USE_TLS", True)
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bloodmgmt.org")
        smtp_configured = bool(getattr(settings, "EMAIL_HOST_USER", ""))

        data = {
            "smtp_configured": smtp_configured,
            "email_backend": backend_name,
            "default_from_email": from_email,
            "email_host": host,
            "email_port": port,
            "use_tls": use_tls,
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Email Management"],
    summary="Send Controlled Administrator Test Email",
    description="Dispatches a single test email to verify SMTP delivery. Restricted to Super Administrators.",
    request=TestEmailSerializer,
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
    },
)
class TestEmailView(APIView):
    """
    Super Admin endpoint to test outbound email connectivity.
    """
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        serializer = TestEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipient_email = serializer.validated_data["recipient_email"]
        subject = serializer.validated_data["subject"]
        message = serializer.validated_data["message"]

        from .email_service import send_notification_email
        try:
            success = send_notification_email(
                recipient=recipient_email,
                subject=subject,
                message=message,
                fail_silently=False,
            )
            if success:
                return Response(
                    {"success": True, "detail": f"Test email successfully dispatched to {recipient_email}."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"success": False, "detail": "Email dispatch could not be completed by SMTP backend."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"success": False, "detail": f"Email delivery error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

