from django.conf import settings
from django.db import models


class Ticket(models.Model):
    """用户提交的工单。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        PROCESSING = "processing", "处理中"
        RESOLVED = "resolved", "已解决"
        CLOSED = "closed", "已关闭"

    class Priority(models.TextChoices):
        LOW = "low", "低"
        MEDIUM = "medium", "中"
        HIGH = "high", "高"
        URGENT = "urgent", "紧急"

    class Category(models.TextChoices):
        ACCOUNT = "account", "账号问题"
        PAYMENT = "payment", "支付问题"
        TECHNICAL = "technical", "技术问题"
        SUGGESTION = "suggestion", "意见建议"
        OTHER = "other", "其他"

    title = models.CharField(
        "工单标题",
        max_length=200,
    )

    description = models.TextField(
        "问题描述",
    )

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tickets",
        verbose_name="创建人",
    )

    status = models.CharField(
        "处理状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    priority = models.CharField(
        "优先级",
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    category = models.CharField(
        "问题分类",
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )

    ai_summary = models.TextField(
        "AI 问题摘要",
        blank=True,
        default="",
    )

    ai_suggested_reply = models.TextField(
        "AI 建议回复",
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True,
    )

    class Meta:
        verbose_name = "工单"
        verbose_name_plural = "工单"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        if self.pk:
            return f"#{self.pk} {self.title}"

        return self.title


class Comment(models.Model):
    """工单下的用户或客服留言。"""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="所属工单",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ticket_comments",
        verbose_name="留言人",
    )

    content = models.TextField(
        "留言内容",
    )

    created_at = models.DateTimeField(
        "留言时间",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "工单留言"
        verbose_name_plural = "工单留言"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"工单 #{self.ticket_id} - {self.author}"