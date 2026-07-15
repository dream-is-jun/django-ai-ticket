from rest_framework import (
    status as http_status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.exceptions import (
    PermissionDenied,
)
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response

from tickets.models import Comment, Ticket

from .permissions import IsTicketOwnerOrStaff
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    StaffTicketSerializer,
    UserTicketSerializer,
)


class TicketViewSet(
    viewsets.ModelViewSet
):
    """工单 REST API。"""

    permission_classes = (
        IsAuthenticated,
        IsTicketOwnerOrStaff,
    )

    def get_queryset(self):
        queryset = (
            Ticket.objects
            .select_related("creator")
            .prefetch_related(
                "comments__author"
            )
            .order_by("-created_at")
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(
            creator=self.request.user
        )

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return StaffTicketSerializer

        return UserTicketSerializer

    def perform_create(self, serializer):
        serializer.save(
            creator=self.request.user,
            status=Ticket.Status.PENDING,
        )

    def perform_update(self, serializer):
        ticket = serializer.instance

        if (
            not self.request.user.is_staff
            and ticket.status
            != Ticket.Status.PENDING
        ):
            raise PermissionDenied(
                "只有待处理工单可以修改。"
            )

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        ticket = self.get_object()

        if (
            not request.user.is_staff
            and ticket.status
            != Ticket.Status.PENDING
        ):
            raise PermissionDenied(
                "只有待处理工单可以删除。"
            )

        ticket.delete()

        return Response(
            status=http_status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="comments",
    )
    def add_comment(
        self,
        request,
        pk=None,
    ):
        ticket = self.get_object()

        if (
            ticket.status == Ticket.Status.CLOSED
            and not request.user.is_staff
        ):
            raise PermissionDenied(
                "工单已经关闭，不能继续留言。"
            )

        input_serializer = (
            CommentCreateSerializer(
                data=request.data
            )
        )

        input_serializer.is_valid(
            raise_exception=True
        )

        comment = Comment.objects.create(
            ticket=ticket,
            author=request.user,
            content=input_serializer.validated_data[
                "content"
            ],
        )

        if (
            request.user.is_staff
            and ticket.status
            == Ticket.Status.PENDING
        ):
            ticket.status = (
                Ticket.Status.PROCESSING
            )

            ticket.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        output_serializer = CommentSerializer(
            comment
        )

        return Response(
            output_serializer.data,
            status=http_status.HTTP_201_CREATED,
        )