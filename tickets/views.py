import logging
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import (

    get_object_or_404,
    redirect,
    render,
)
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import (
    CommentForm,
    RegisterForm,
    StaffTicketUpdateForm,
    TicketForm,
)
from .services.qwen_service import (
    QwenServiceError,
    analyze_ticket,
)
from .models import Comment, Ticket

logger = logging.getLogger(__name__)
def home(request: HttpRequest) -> HttpResponse:
    """网站首页。"""

    if request.user.is_authenticated:
        return redirect("tickets:ticket_list")

    return render(
        request,
        "tickets/home.html",
    )


def register(request: HttpRequest) -> HttpResponse:
    """普通用户注册。"""

    if request.user.is_authenticated:
        return redirect("tickets:ticket_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            messages.success(
                request,
                "注册成功，你已经自动登录。",
            )

            return redirect(
                "tickets:ticket_list"
            )

    else:
        form = RegisterForm()

    return render(
        request,
        "tickets/register.html",
        {
            "form": form,
        },
    )


def get_visible_tickets(user):
    """
    返回当前用户有权查看的工单。

    普通用户只能查看自己的工单；
    管理员或客服可以查看全部工单。
    """

    queryset = (
        Ticket.objects
        .select_related("creator")
        .prefetch_related("comments__author")
    )

    if user.is_staff:
        return queryset

    return queryset.filter(
        creator=user
    )


def get_owned_ticket_or_404(user, pk: int) -> Ticket:
    """
    获取当前用户自己创建的工单。

    查不到工单或工单不属于当前用户时，
    均返回 404。
    """

    queryset = (
        Ticket.objects
        .select_related("creator")
        .prefetch_related("comments__author")
    )

    return get_object_or_404(
        queryset,
        pk=pk,
        creator=user,
    )


@login_required
def ticket_list(
    request: HttpRequest,
) -> HttpResponse:
    """搜索、筛选并分页显示工单。"""

    tickets = get_visible_tickets(
        request.user
    ).order_by("-created_at")

    query = request.GET.get(
        "q",
        "",
    ).strip()

    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    selected_category = request.GET.get(
        "category",
        "",
    ).strip()

    selected_priority = request.GET.get(
        "priority",
        "",
    ).strip()

    if query:
        tickets = tickets.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(creator__username__icontains=query)
        )

    valid_statuses = {
        value
        for value, _label
        in Ticket.Status.choices
    }

    valid_categories = {
        value
        for value, _label
        in Ticket.Category.choices
    }

    valid_priorities = {
        value
        for value, _label
        in Ticket.Priority.choices
    }

    if selected_status in valid_statuses:
        tickets = tickets.filter(
            status=selected_status
        )

    if selected_category in valid_categories:
        tickets = tickets.filter(
            category=selected_category
        )

    if selected_priority in valid_priorities:
        tickets = tickets.filter(
            priority=selected_priority
        )

    paginator = Paginator(
        tickets,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "tickets/ticket_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "selected_status": selected_status,
            "selected_category": selected_category,
            "selected_priority": selected_priority,
            "status_choices": Ticket.Status.choices,
            "category_choices": Ticket.Category.choices,
            "priority_choices": Ticket.Priority.choices,
        },
    )


@login_required
def ticket_detail(
    request: HttpRequest,
    pk: int,
) -> HttpResponse:
    """显示一条工单的详情。"""

    visible_tickets = get_visible_tickets(
        request.user
    )

    ticket = get_object_or_404(
        visible_tickets,
        pk=pk,
    )

    context = {
        "ticket": ticket,
        "comment_form": CommentForm(),
    }

    if request.user.is_staff:
        context["staff_form"] = (
            StaffTicketUpdateForm(
                instance=ticket
            )
        )

    return render(
        request,
        "tickets/ticket_detail.html",
        context,
    )

@login_required
def ticket_create(
    request: HttpRequest,
) -> HttpResponse:
    """普通用户创建工单。"""

    if request.method == "POST":
        form = TicketForm(request.POST)

        if form.is_valid():
            # 暂时创建对象，但先不写入数据库
            ticket = form.save(commit=False)

            # 创建人必须由服务器根据当前登录用户设置
            ticket.creator = request.user

            # 新工单固定为待处理状态
            ticket.status = Ticket.Status.PENDING

            ticket.save()

            messages.success(
                request,
                f"工单 #{ticket.pk} 创建成功。",
            )

            return redirect(
                "tickets:ticket_detail",
                pk=ticket.pk,
            )

    else:
        form = TicketForm()

    return render(
        request,
        "tickets/ticket_form.html",
        {
            "form": form,
            "page_title": "创建工单",
            "submit_text": "提交工单",
        },
    )


@login_required
def ticket_update(
    request: HttpRequest,
    pk: int,
) -> HttpResponse:
    """修改当前用户自己的待处理工单。"""

    ticket = get_owned_ticket_or_404(
        request.user,
        pk,
    )

    if ticket.status != Ticket.Status.PENDING:
        messages.warning(
            request,
            "只有处于“待处理”状态的工单可以修改。",
        )

        return redirect(
            "tickets:ticket_detail",
            pk=ticket.pk,
        )

    if request.method == "POST":
        form = TicketForm(
            request.POST,
            instance=ticket,
        )

        if form.is_valid():
            updated_ticket = form.save()

            messages.success(
                request,
                f"工单 #{updated_ticket.pk} 修改成功。",
            )

            return redirect(
                "tickets:ticket_detail",
                pk=updated_ticket.pk,
            )

    else:
        form = TicketForm(
            instance=ticket,
        )

    return render(
        request,
        "tickets/ticket_form.html",
        {
            "form": form,
            "ticket": ticket,
            "page_title": "修改工单",
            "submit_text": "保存修改",
        },
    )


@login_required
def ticket_delete(
    request: HttpRequest,
    pk: int,
) -> HttpResponse:
    """删除当前用户自己的待处理工单。"""

    ticket = get_owned_ticket_or_404(
        request.user,
        pk,
    )

    if ticket.status != Ticket.Status.PENDING:
        messages.warning(
            request,
            "只有处于“待处理”状态的工单可以删除。",
        )

        return redirect(
            "tickets:ticket_detail",
            pk=ticket.pk,
        )

    if request.method == "POST":
        ticket_number = ticket.pk
        ticket_title = ticket.title

        ticket.delete()

        messages.success(
            request,
            (
                f"工单 #{ticket_number} "
                f"“{ticket_title}”已经删除。"
            ),
        )

        return redirect(
            "tickets:ticket_list"
        )

    return render(
        request,
        "tickets/ticket_confirm_delete.html",
        {
            "ticket": ticket,
        },
    )
@login_required
@require_POST
def comment_create(
    request: HttpRequest,
    pk: int,
) -> HttpResponse:
    """给当前用户有权访问的工单追加留言。"""

    visible_tickets = get_visible_tickets(
        request.user
    )

    ticket = get_object_or_404(
        visible_tickets,
        pk=pk,
    )

    if (
        ticket.status == Ticket.Status.CLOSED
        and not request.user.is_staff
    ):
        messages.warning(
            request,
            "工单已经关闭，不能继续追加留言。",
        )

        return redirect(
            "tickets:ticket_detail",
            pk=ticket.pk,
        )

    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)

        comment.ticket = ticket
        comment.author = request.user

        comment.save()

        # 客服首次回复后，自动进入“处理中”
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

        messages.success(
            request,
            "留言已经提交。",
        )

    else:
        messages.error(
            request,
            "留言提交失败，请检查留言内容。",
        )

    return redirect(
        "tickets:ticket_detail",
        pk=ticket.pk,
    )


@login_required
@require_POST
def staff_ticket_update(
    request: HttpRequest,
    pk: int,
) -> HttpResponse:
    """客服或管理员修改工单处理信息。"""

    if not request.user.is_staff:
        raise PermissionDenied(
            "只有客服或管理员可以处理工单。"
        )

    ticket = get_object_or_404(
        Ticket,
        pk=pk,
    )

    form = StaffTicketUpdateForm(
        request.POST,
        instance=ticket,
    )

    if form.is_valid():
        form.save()

        messages.success(
            request,
            f"工单 #{ticket.pk} 的处理信息已经更新。",
        )

    else:
        messages.error(
            request,
            "处理信息更新失败。",
        )

    return redirect(
        "tickets:ticket_detail",
        pk=ticket.pk,
    )
@login_required
@require_POST
def ticket_ai_analyze(
    request: HttpRequest,
    pk: int,
) -> HttpResponse:
    """让通义千问分析工单。"""

    if not request.user.is_staff:
        raise PermissionDenied(
            "只有客服或管理员可以使用 AI 分析。"
        )

    ticket = get_object_or_404(
        Ticket,
        pk=pk,
    )

    try:
        result = analyze_ticket(ticket)

    except QwenServiceError as exc:
        logger.exception(
            "AI 分析工单失败，ticket_id=%s",
            ticket.pk,
        )

        messages.error(
            request,
            f"AI 分析失败：{exc}",
        )

    else:
        ticket.ai_summary = result.summary
        ticket.ai_suggested_reply = (
            result.suggested_reply
        )
        ticket.category = result.category
        ticket.priority = result.priority

        ticket.save()

        messages.success(
            request,
            "AI 分析已经完成。",
        )

    return redirect(
        "tickets:ticket_detail",
        pk=ticket.pk,
    )


@login_required
@require_POST
def ticket_use_ai_reply(
    request: HttpRequest,
    pk: int,
) -> HttpResponse:
    """将 AI 建议回复保存成客服留言。"""

    if not request.user.is_staff:
        raise PermissionDenied(
            "只有客服或管理员可以采用 AI 回复。"
        )

    ticket = get_object_or_404(
        Ticket,
        pk=pk,
    )

    suggested_reply = (
        ticket.ai_suggested_reply.strip()
    )

    if not suggested_reply:
        messages.warning(
            request,
            "当前工单还没有 AI 建议回复。",
        )

        return redirect(
            "tickets:ticket_detail",
            pk=ticket.pk,
        )

    Comment.objects.create(
        ticket=ticket,
        author=request.user,
        content=suggested_reply,
    )

    if ticket.status == Ticket.Status.PENDING:
        ticket.status = Ticket.Status.PROCESSING

        ticket.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    messages.success(
        request,
        "AI 建议回复已经作为客服留言发送。",
    )

    return redirect(
        "tickets:ticket_detail",
        pk=ticket.pk,
    )
@login_required
def dashboard(
    request: HttpRequest,
) -> HttpResponse:
    """显示当前用户有权查看的工单统计。"""

    tickets = get_visible_tickets(
        request.user
    )

    status_cards = [
        {
            "value": value,
            "label": label,
            "count": tickets.filter(
                status=value
            ).count(),
        }
        for value, label
        in Ticket.Status.choices
    ]

    category_cards = [
        {
            "value": value,
            "label": label,
            "count": tickets.filter(
                category=value
            ).count(),
        }
        for value, label
        in Ticket.Category.choices
    ]

    context = {
        "total_count": tickets.count(),
        "urgent_count": tickets.filter(
            priority=Ticket.Priority.URGENT
        ).count(),
        "status_cards": status_cards,
        "category_cards": category_cards,
        "recent_tickets": tickets.order_by(
            "-created_at"
        )[:5],
    }

    return render(
        request,
        "tickets/dashboard.html",
        context,
    )
def health_check(
    request: HttpRequest,
) -> JsonResponse:
    """部署平台健康检查。"""

    return JsonResponse(
        {
            "status": "ok"
        }
    )