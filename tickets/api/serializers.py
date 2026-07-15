from rest_framework import serializers

from tickets.models import Comment, Ticket


class CommentSerializer(
    serializers.ModelSerializer
):
    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
    )

    class Meta:
        model = Comment

        fields = (
            "id",
            "author_username",
            "content",
            "created_at",
        )

        read_only_fields = (
            "id",
            "author_username",
            "created_at",
        )


class TicketBaseSerializer(
    serializers.ModelSerializer
):
    creator_username = serializers.CharField(
        source="creator.username",
        read_only=True,
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    category_display = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )

    priority_display = serializers.CharField(
        source="get_priority_display",
        read_only=True,
    )

    comments = CommentSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Ticket

        fields = (
            "id",
            "title",
            "description",
            "creator_username",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "category",
            "category_display",
            "ai_summary",
            "ai_suggested_reply",
            "created_at",
            "updated_at",
            "comments",
        )

        read_only_fields = (
            "id",
            "creator_username",
            "status_display",
            "priority_display",
            "category_display",
            "ai_summary",
            "ai_suggested_reply",
            "created_at",
            "updated_at",
            "comments",
        )

    def validate_title(
        self,
        value: str,
    ) -> str:
        value = value.strip()

        if len(value) < 4:
            raise serializers.ValidationError(
                "工单标题至少需要 4 个字符。"
            )

        return value

    def validate_description(
        self,
        value: str,
    ) -> str:
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "问题描述至少需要 10 个字符。"
            )

        return value


class UserTicketSerializer(
    TicketBaseSerializer
):
    """普通用户使用的工单序列化器。"""

    class Meta(TicketBaseSerializer.Meta):
        read_only_fields = (
            TicketBaseSerializer.Meta.read_only_fields
            + (
                "status",
            )
        )


class StaffTicketSerializer(
    TicketBaseSerializer
):
    """客服或管理员使用的序列化器。"""


class CommentCreateSerializer(
    serializers.Serializer
):
    """API 添加留言时使用。"""

    content = serializers.CharField(
        min_length=2,
        max_length=2000,
        trim_whitespace=True,
    )