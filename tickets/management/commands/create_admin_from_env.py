import os

from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
)


User = get_user_model()


class Command(BaseCommand):
    help = "根据环境变量创建线上管理员"

    def handle(self, *args, **options):
        username = os.getenv(
            "DJANGO_SUPERUSER_USERNAME",
            "",
        ).strip()

        email = os.getenv(
            "DJANGO_SUPERUSER_EMAIL",
            "",
        ).strip()

        password = os.getenv(
            "DJANGO_SUPERUSER_PASSWORD",
            "",
        )

        if not username or not password:
            self.stdout.write(
                "未配置线上管理员环境变量，跳过。"
            )
            return

        user, created = (
            User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
        )

        if created:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "线上管理员创建成功。"
                )
            )

        else:
            self.stdout.write(
                "管理员已经存在，跳过创建。"
            )