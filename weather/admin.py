from django.contrib import admin

from .models import Alert, City, DailyForecast, Favorite, MemberProfile


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "slug", "lat", "lon")
    search_fields = ("name", "region")


@admin.register(DailyForecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = (
        "city", "date", "temp_high_c", "temp_low_c",
        "precip_pct", "wind_kmh", "condition", "best_time_hint",
    )
    list_filter = ("city", "condition")
    search_fields = ("city__name",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "title", "severity", "area", "starts_at", "ends_at", "is_active",
    )
    list_filter = ("severity", "is_active", "city")
    search_fields = ("title", "area")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "created_at")


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "notify_channel", "min_severity")
