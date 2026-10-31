from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),
    path("", include("forecast.urls")),
]

handler404 = "forecast.views.not_found"
