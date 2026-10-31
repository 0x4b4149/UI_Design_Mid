from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("locations/", views.locations, name="locations"),
    path("locations/<slug:slug>/", views.location_detail, name="location_detail"),
    path("alerts/", views.alerts, name="alerts"),
    path("alerts/<int:pk>/", views.alert_detail, name="alert_detail"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("favorites/<slug:slug>/toggle/", views.toggle_favorite, name="toggle_favorite"),
    path("preferences/unit/<str:unit>/", views.set_unit, name="set_unit"),
    path("accounts/login/", views.SkylineLoginView.as_view(), name="login"),
    path("accounts/register/", views.register, name="register"),
    path("api/search/", views.search_suggestions, name="search_suggestions"),
    path("healthz/", views.healthz, name="healthz"),
]
