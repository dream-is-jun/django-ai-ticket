from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "accounts/",
        include(
            "django.contrib.auth.urls"
        ),
    ),

    path(
        "api/",
        include("tickets.api.urls"),
    ),

    path(
        "api-auth/",
        include(
            "rest_framework.urls"
        ),
    ),

    path(
        "",
        include("tickets.urls"),
    ),
]