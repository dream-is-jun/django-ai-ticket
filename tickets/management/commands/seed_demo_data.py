from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
)

from tickets.models import Comment, Ticket


User = get_user_model()


class Command(BaseCommand):
    help = "创建项目演示用户和演示工单"

    def handle(self, *args, **options):
        demo_user, _created = (
            User.objects.get_or_create(
                username="demo_user",
                defaults={
                    "email": "demo@example.com",
                },
            )
        )

        demo_user.set_password(
            "DemoUser2026!"
        )
        demo_user.save()

        staff_user, _created = (
            User.objects.get_or_create(
                username="demo_staff",
                defaults={
                    "email": "staff@example.com",
                    "is_staff": True,
                },
            )
        )

        staff_user.is_staff = True
        staff_user.set_password(
            "DemoStaff2026!"
        )
        staff_user.save()

        ticket, _created = (
            Ticket.objects.get_or_create(
                title="演示：登录系统时提示账号异常",
                creator=demo_user,
                defaults={
                    "description": (
                        "用户输入正确用户名和密码后，"
                        "系统仍然提示账号异常，"
                        "无法进入个人中心。"
                    ),
                    "category": (
                        Ticket.Category.ACCOUNT
                    ),
                    "priority": (
                        Ticket.Priority.HIGH
                    ),
                    "status": (
                        Ticket.Status.PROCESSING
                    ),
                },
            )
        )

        Comment.objects.get_or_create(
            ticket=ticket,
            author=staff_user,
            content=(
                "您好，我们已经开始检查您的账号状态。"
            ),
        )

        self.stdout.write(
            self.style.SUCCESS(
                "演示数据创建完成。\n"
                "普通用户：demo_user / DemoUser2026!\n"
                "客服用户：demo_staff / DemoStaff2026!"
            )
        )