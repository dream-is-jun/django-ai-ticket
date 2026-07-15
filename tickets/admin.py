from django.contrib import admin

from .models import Comment, Ticket


class CommentInline(admin.TabularInline):
    """在工单编辑页中直接显示留言。"""

    model = Comment
    extra = 0
    fields = (
        "author",
        "content",
        "created_at",
    )
    readonly_fields = (
        "created_at",
    )
    show_change_link = True


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """工单后台管理配置。"""

    list_display = (
        "id",
        "title",
        "creator",
        "category",
        "priority",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "priority",
        "category",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "creator__username",
        "ai_summary",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "creator",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )

    list_per_page = 20

    inlines = (
        CommentInline,
    )

    fieldsets = (
        (
            "工单基本信息",
            {
                "fields": (
                    "title",
                    "description",
                    "creator",
                )
            },
        ),
        (
            "处理信息",
            {
                "fields": (
                    "category",
                    "priority",
                    "status",
                )
            },
        ),
        (
            "AI 分析结果",
            {
                "fields": (
                    "ai_summary",
                    "ai_suggested_reply",
                )
            },
        ),
        (
            "时间信息",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """工单留言后台管理配置。"""

    list_display = (
        "id",
        "ticket",
        "author",
        "short_content",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "content",
        "ticket__title",
        "author__username",
    )

    readonly_fields = (
        "created_at",
    )

    list_select_related = (
        "ticket",
        "author",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="留言内容")
    def short_content(self, obj: Comment) -> str:
        if len(obj.content) > 40:
            return f"{obj.content[:40]}..."

        return obj.content


admin.site.site_header = "AI 智能工单管理后台"
admin.site.site_title = "AI 工单系统"
admin.site.index_title = "后台管理"