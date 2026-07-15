from django.urls import path

from . import views


app_name = "tickets"


urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "register/",
        views.register,
        name="register",
    ),

    path(
        "tickets/",
        views.ticket_list,
        name="ticket_list",
    ),

    path(
        "tickets/create/",
        views.ticket_create,
        name="ticket_create",
    ),

    path(
        "tickets/<int:pk>/",
        views.ticket_detail,
        name="ticket_detail",
    ),

    path(
        "tickets/<int:pk>/edit/",
        views.ticket_update,
        name="ticket_update",
    ),

    path(
        "tickets/<int:pk>/delete/",
        views.ticket_delete,
        name="ticket_delete",
    ),
    path(
    "tickets/<int:pk>/comments/add/",
    views.comment_create,
    name="comment_create",
    ),

    path(
    "tickets/<int:pk>/staff-update/",
    views.staff_ticket_update,
    name="staff_ticket_update",
    ),
    path(
    "tickets/<int:pk>/ai-analyze/",
    views.ticket_ai_analyze,
    name="ticket_ai_analyze",
    ),

    path(
    "tickets/<int:pk>/use-ai-reply/",
    views.ticket_use_ai_reply,
    name="ticket_use_ai_reply",
    ),
    path(
    "dashboard/",
    views.dashboard,
    name="dashboard",
    ),
    path(
    "health/",
    views.health_check,
    name="health_check",
    ),
]