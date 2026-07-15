from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from rest_framework import (
    status as http_status,
)
from rest_framework.test import APITestCase

from .models import Comment, Ticket
from .services.qwen_service import (
    TicketAIResult,
)




User = get_user_model()


class TicketAccessTests(TestCase):
    """测试工单登录和数据隔离。"""

    def setUp(self):
        self.password = "TestPass2026!"

        self.alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password=self.password,
        )

        self.bob = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password=self.password,
        )

        self.alice_ticket = Ticket.objects.create(
            title="Alice 的账号问题",
            description="Alice 输入密码后无法正常登录系统。",
            creator=self.alice,
            category=Ticket.Category.ACCOUNT,
        )

        self.bob_ticket = Ticket.objects.create(
            title="Bob 的支付问题",
            description="Bob 在提交订单时无法完成支付操作。",
            creator=self.bob,
            category=Ticket.Category.PAYMENT,
        )

    def test_anonymous_user_is_redirected_to_login(
        self,
    ):
        response = self.client.get(
            reverse("tickets:ticket_list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_user_only_sees_own_tickets(
        self,
    ):
        self.client.login(
            username="alice",
            password=self.password,
        )

        response = self.client.get(
            reverse("tickets:ticket_list")
        )

        self.assertContains(
            response,
            "Alice 的账号问题",
        )

        self.assertNotContains(
            response,
            "Bob 的支付问题",
        )

    def test_user_cannot_open_other_users_ticket(
        self,
    ):
        self.client.login(
            username="alice",
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tickets:ticket_detail",
                args=[self.bob_ticket.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_staff_user_can_see_all_tickets(
        self,
    ):
        staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password=self.password,
            is_staff=True,
        )

        self.client.login(
            username="staff",
            password=self.password,
        )

        response = self.client.get(
            reverse("tickets:ticket_list")
        )

        self.assertContains(
            response,
            "Alice 的账号问题",
        )

        self.assertContains(
            response,
            "Bob 的支付问题",
        )


class TicketCrudTests(TestCase):
    """测试普通用户对工单的增删改查。"""

    def setUp(self):
        self.password = "TestPass2026!"

        self.alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password=self.password,
        )

        self.bob = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password=self.password,
        )

        self.ticket = Ticket.objects.create(
            title="原始测试工单",
            description="这是一张用于测试修改和删除功能的工单。",
            creator=self.alice,
            category=Ticket.Category.TECHNICAL,
            priority=Ticket.Priority.MEDIUM,
            status=Ticket.Status.PENDING,
        )

    def test_anonymous_user_cannot_create_ticket(
        self,
    ):
        response = self.client.get(
            reverse("tickets:ticket_create")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_logged_in_user_can_create_ticket(
        self,
    ):
        self.client.login(
            username="alice",
            password=self.password,
        )

        response = self.client.post(
            reverse("tickets:ticket_create"),
            data={
                "title": "系统无法保存用户资料",
                "description": (
                    "用户修改个人资料后点击保存，"
                    "页面提示保存失败。"
                ),
                "category": Ticket.Category.TECHNICAL,
                "priority": Ticket.Priority.HIGH,
            },
        )

        created_ticket = Ticket.objects.get(
            title="系统无法保存用户资料"
        )

        self.assertRedirects(
            response,
            reverse(
                "tickets:ticket_detail",
                args=[created_ticket.pk],
            ),
        )

        self.assertEqual(
            created_ticket.creator,
            self.alice,
        )

        self.assertEqual(
            created_ticket.status,
            Ticket.Status.PENDING,
        )

    def test_invalid_short_content_is_rejected(
        self,
    ):
        self.client.login(
            username="alice",
            password=self.password,
        )

        original_count = Ticket.objects.count()

        response = self.client.post(
            reverse("tickets:ticket_create"),
            data={
                "title": "短",
                "description": "太短",
                "category": Ticket.Category.OTHER,
                "priority": Ticket.Priority.LOW,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Ticket.objects.count(),
            original_count,
        )

        self.assertContains(
            response,
            "工单标题至少需要 4 个字符。",
        )

        self.assertContains(
            response,
            "问题描述至少需要 10 个字符。",
        )

    def test_owner_can_update_pending_ticket(
        self,
    ):
        self.client.login(
            username="alice",
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tickets:ticket_update",
                args=[self.ticket.pk],
            ),
            data={
                "title": "修改后的测试工单",
                "description": (
                    "这是修改后的问题描述，"
                    "用于确认工单更新功能正常。"
                ),
                "category": Ticket.Category.ACCOUNT,
                "priority": Ticket.Priority.HIGH,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "tickets:ticket_detail",
                args=[self.ticket.pk],
            ),
        )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.title,
            "修改后的测试工单",
        )

        self.assertEqual(
            self.ticket.category,
            Ticket.Category.ACCOUNT,
        )

    def test_user_cannot_update_other_users_ticket(
        self,
    ):
        self.client.login(
            username="bob",
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tickets:ticket_update",
                args=[self.ticket.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_owner_cannot_update_resolved_ticket(
        self,
    ):
        self.ticket.status = Ticket.Status.RESOLVED
        self.ticket.save(
            update_fields=["status"]
        )

        self.client.login(
            username="alice",
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tickets:ticket_update",
                args=[self.ticket.pk],
            ),
            data={
                "title": "不应该被保存的新标题",
                "description": (
                    "这段内容不应该保存到已经解决的工单。"
                ),
                "category": Ticket.Category.OTHER,
                "priority": Ticket.Priority.LOW,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "tickets:ticket_detail",
                args=[self.ticket.pk],
            ),
        )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.title,
            "原始测试工单",
        )

    def test_get_delete_page_does_not_delete_ticket(
        self,
    ):
        self.client.login(
            username="alice",
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tickets:ticket_delete",
                args=[self.ticket.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            Ticket.objects.filter(
                pk=self.ticket.pk
            ).exists()
        )

    def test_owner_can_delete_pending_ticket(
        self,
    ):
        self.client.login(
            username="alice",
            password=self.password,
        )

        ticket_id = self.ticket.pk

        response = self.client.post(
            reverse(
                "tickets:ticket_delete",
                args=[ticket_id],
            )
        )

        self.assertRedirects(
            response,
            reverse("tickets:ticket_list"),
        )

        self.assertFalse(
            Ticket.objects.filter(
                pk=ticket_id
            ).exists()
        )

    def test_user_cannot_delete_other_users_ticket(
        self,
    ):
        self.client.login(
            username="bob",
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tickets:ticket_delete",
                args=[self.ticket.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertTrue(
            Ticket.objects.filter(
                pk=self.ticket.pk
            ).exists()
        )
class CommentWorkflowTests(TestCase):
    """测试工单留言和状态流转。"""

    def setUp(self):
        self.password = "TestPass2026!"

        self.user = User.objects.create_user(
            username="user1",
            password=self.password,
        )

        self.other_user = (
            User.objects.create_user(
                username="user2",
                password=self.password,
            )
        )

        self.staff = User.objects.create_user(
            username="staff",
            password=self.password,
            is_staff=True,
        )

        self.ticket = Ticket.objects.create(
            title="留言测试工单",
            description=(
                "这是一张用于测试留言和状态流转的工单。"
            ),
            creator=self.user,
        )

    def test_owner_can_add_comment(self):
        self.client.login(
            username="user1",
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tickets:comment_create",
                args=[self.ticket.pk],
            ),
            {
                "content": "这是用户追加的留言。",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "tickets:ticket_detail",
                args=[self.ticket.pk],
            ),
        )

        self.assertEqual(
            Comment.objects.count(),
            1,
        )

    def test_other_user_cannot_add_comment(self):
        self.client.login(
            username="user2",
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tickets:comment_create",
                args=[self.ticket.pk],
            ),
            {
                "content": "不应该被保存。",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            Comment.objects.count(),
            0,
        )

    def test_staff_reply_moves_ticket_to_processing(
        self,
    ):
        self.client.login(
            username="staff",
            password=self.password,
        )

        self.client.post(
            reverse(
                "tickets:comment_create",
                args=[self.ticket.pk],
            ),
            {
                "content": "客服已经开始处理。",
            },
        )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.status,
            Ticket.Status.PROCESSING,
        )


class TicketAITests(TestCase):
    """测试 AI 分析视图。"""

    def setUp(self):
        self.password = "TestPass2026!"

        self.staff = User.objects.create_user(
            username="staff",
            password=self.password,
            is_staff=True,
        )

        self.ticket = Ticket.objects.create(
            title="无法登录账号",
            description=(
                "用户输入正确密码后仍然无法登录系统。"
            ),
            creator=self.staff,
        )

    @patch(
        "tickets.views.analyze_ticket"
    )
    def test_staff_can_analyze_ticket(
        self,
        mock_analyze,
    ):
        mock_analyze.return_value = (
            TicketAIResult(
                summary="用户无法正常登录账号。",
                category=Ticket.Category.ACCOUNT,
                priority=Ticket.Priority.HIGH,
                suggested_reply=(
                    "请尝试重置密码并检查账号状态。"
                ),
            )
        )

        self.client.login(
            username="staff",
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tickets:ticket_ai_analyze",
                args=[self.ticket.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "tickets:ticket_detail",
                args=[self.ticket.pk],
            ),
        )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.category,
            Ticket.Category.ACCOUNT,
        )

        self.assertEqual(
            self.ticket.priority,
            Ticket.Priority.HIGH,
        )

        self.assertEqual(
            self.ticket.ai_summary,
            "用户无法正常登录账号。",
        )


class TicketAPITests(APITestCase):
    """测试工单 REST API。"""

    def setUp(self):
        self.password = "TestPass2026!"

        self.user = User.objects.create_user(
            username="api_user",
            password=self.password,
        )

        self.other_user = (
            User.objects.create_user(
                username="other_user",
                password=self.password,
            )
        )

        self.ticket = Ticket.objects.create(
            title="自己的 API 工单",
            description=(
                "这是一张属于当前用户的 API 工单。"
            ),
            creator=self.user,
        )

        Ticket.objects.create(
            title="其他用户的 API 工单",
            description=(
                "这是一张不应该被当前用户看到的工单。"
            ),
            creator=self.other_user,
        )

    def test_api_only_returns_own_tickets(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            reverse("ticket-list")
        )

        self.assertEqual(
            response.status_code,
            http_status.HTTP_200_OK,
        )

        titles = [
            item["title"]
            for item in response.data["results"]
        ]

        self.assertIn(
            "自己的 API 工单",
            titles,
        )

        self.assertNotIn(
            "其他用户的 API 工单",
            titles,
        )

    def test_api_create_sets_current_user(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            reverse("ticket-list"),
            {
                "title": "通过 API 新建的工单",
                "description": (
                    "这是一张通过 API 新建的工单。"
                ),
                "category": Ticket.Category.TECHNICAL,
                "priority": Ticket.Priority.HIGH,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            http_status.HTTP_201_CREATED,
        )

        ticket = Ticket.objects.get(
            title="通过 API 新建的工单"
        )

        self.assertEqual(
            ticket.creator,
            self.user,
        )

        self.assertEqual(
            ticket.status,
            Ticket.Status.PENDING,
        )

    def test_api_can_add_comment(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            reverse(
                "ticket-add-comment",
                args=[self.ticket.pk],
            ),
            {
                "content": "API 追加留言。",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            http_status.HTTP_201_CREATED,
        )

        self.assertEqual(
            self.ticket.comments.count(),
            1,
        )