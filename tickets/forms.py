from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Comment, Ticket


User = get_user_model()


class RegisterForm(UserCreationForm):
    """普通用户注册表单。"""

    email = forms.EmailField(
        label="电子邮箱",
        required=True,
        help_text="请输入可以正常使用的电子邮箱。",
    )

    class Meta(UserCreationForm.Meta):
        model = User

        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].label = "用户名"
        self.fields["password1"].label = "密码"
        self.fields["password2"].label = "确认密码"

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_email(self) -> str:
        """检查邮箱是否已经注册。"""

        email = self.cleaned_data["email"].strip().lower()

        email_exists = User.objects.filter(
            email__iexact=email
        ).exists()

        if email_exists:
            raise forms.ValidationError(
                "这个电子邮箱已经被注册。"
            )

        return email

    def save(self, commit: bool = True):
        """保存用户，同时保存邮箱。"""

        user = super().save(commit=False)

        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

        return user


class TicketForm(forms.ModelForm):
    """普通用户创建和修改工单时使用的表单。"""

    class Meta:
        model = Ticket

        # 只允许普通用户填写以下四个字段
        fields = (
            "title",
            "description",
            "category",
            "priority",
        )

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "例如：登录系统时提示账号异常",
                    "maxlength": "200",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "placeholder": (
                        "请详细描述发生时间、操作步骤、"
                        "错误提示以及已经尝试过的解决方法。"
                    ),
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

        help_texts = {
            "title": "请用一句话概括问题，至少填写 4 个字符。",
            "description": "请尽量详细描述问题，至少填写 10 个字符。",
            "category": "请选择最符合当前问题的分类。",
            "priority": "请根据问题对工作的影响程度选择优先级。",
        }

    def clean_title(self) -> str:
        """清理并验证工单标题。"""

        title = self.cleaned_data["title"].strip()

        if len(title) < 4:
            raise forms.ValidationError(
                "工单标题至少需要 4 个字符。"
            )

        return title

    def clean_description(self) -> str:
        """清理并验证问题描述。"""

        description = self.cleaned_data["description"].strip()

        if len(description) < 10:
            raise forms.ValidationError(
                "问题描述至少需要 10 个字符。"
            )

        return description
class CommentForm(forms.ModelForm):
    """用户或客服追加工单留言时使用的表单。"""

    class Meta:
        model = Comment

        fields = (
            "content",
        )

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "请输入需要补充的内容……",
                }
            ),
        }

        labels = {
            "content": "留言内容",
        }

    def clean_content(self) -> str:
        content = self.cleaned_data["content"].strip()

        if len(content) < 2:
            raise forms.ValidationError(
                "留言至少需要填写 2 个字符。"
            )

        if len(content) > 2000:
            raise forms.ValidationError(
                "留言不能超过 2000 个字符。"
            )

        return content


class StaffTicketUpdateForm(forms.ModelForm):
    """客服或管理员处理工单时使用的表单。"""

    class Meta:
        model = Ticket

        fields = (
            "status",
            "category",
            "priority",
        )

        widgets = {
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }