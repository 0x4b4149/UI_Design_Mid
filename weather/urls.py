from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("city/<slug:slug>/", views.forecast, name="forecast"),
    path("alerts/", views.alerts, name="alerts"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/profile/", views.profile, name="profile"),
    path("accounts/favorite/<int:city_id>/", views.toggle_favorite, name="favorite"),
    path("accounts/favorites/add/", views.add_favorite, name="add_favorite"),
]
