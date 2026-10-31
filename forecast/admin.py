from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import (
    Alert,
    CurrentConditions,
    DailyForecast,
    Favorite,
    HourlyForecast,
    Location,
    Profile,
    SearchHistory,
)

admin.site.site_header = "Skyline Weather 管理後台"
admin.site.site_title = "Skyline Weather Admin"
admin.site.index_title = "網站資料管理"


class CurrentConditionsInline(admin.StackedInline):
    model = CurrentConditions
    extra = 0
    max_num = 1
    verbose_name_plural = "即時觀測"


class DailyForecastInline(admin.TabularInline):
    model = DailyForecast
    extra = 0
    fields = ("date", "condition", "high_f", "low_f", "precip_percent", "wind")


class AlertInline(admin.TabularInline):
    model = Alert
    extra = 0
    fields = ("title", "severity", "alert_type", "starts_at", "ends_at", "is_active")
    show_change_link = True


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "state",
        "region",
        "station_code",
        "current_temp_display",
        "current_condition",
        "active_alert_count",
        "is_featured",
    )
    list_filter = ("region", "is_featured")
    search_fields = ("name", "state", "county", "station_code", "zip_code")
    prepopulated_fields = {"slug": ("name", "state")}
    list_editable = ("is_featured",)
    readonly_fields = ("created_at",)
    inlines = [CurrentConditionsInline, DailyForecastInline, AlertInline]
    fieldsets = (
        ("基本資料", {
            "fields": ("name", "state", "slug", "county", "zip_code", "region", "is_featured")
        }),
        ("地理與測站", {
            "fields": (
                "latitude",
                "longitude",
                "timezone",
                "station_code",
                "elevation_ft",
            )
        }),
        ("內容", {"fields": ("description", "created_at")}),
    )

    @admin.display(description="現在溫度", ordering="current__temp_f")
    def current_temp_display(self, obj):
        current = getattr(obj, "current", None)
        return f"{current.temp_f}°F" if current else "—"

    @admin.display(description="天氣")
    def current_condition(self, obj):
        current = getattr(obj, "current", None)
        return current.get_condition_display() if current else "—"

    @admin.display(description="有效警報")
    def active_alert_count(self, obj):
        count = obj.alerts.filter(is_active=True).count()
        if not count:
            return "0"
        return format_html(
            '<span style="display:inline-block;min-width:20px;padding:1px 8px;'
            'border-radius:999px;background:#FDE9E7;color:#B3251A;font-weight:700;'
            'text-align:center;">{}</span>',
            count,
        )


@admin.register(CurrentConditions)
class CurrentConditionsAdmin(admin.ModelAdmin):
    list_display = (
        "location",
        "temp_f",
        "feels_like_f",
        "condition",
        "humidity",
        "wind_mph",
        "aqi",
        "observed_at",
    )
    list_filter = ("condition", "observed_at")
    search_fields = ("location__name", "location__state")
    autocomplete_fields = ("location",)
    list_select_related = ("location",)


@admin.register(DailyForecast)
class DailyForecastAdmin(admin.ModelAdmin):
    list_display = (
        "location",
        "date",
        "condition",
        "high_f",
        "low_f",
        "precip_percent",
        "wind",
    )
    list_filter = ("condition", "date")
    search_fields = ("location__name", "location__state")
    autocomplete_fields = ("location",)
    date_hierarchy = "date"
    list_select_related = ("location",)


@admin.register(HourlyForecast)
class HourlyForecastAdmin(admin.ModelAdmin):
    list_display = ("location", "time", "temp_f", "condition", "precip_percent", "wind_mph")
    list_filter = ("condition", "time")
    search_fields = ("location__name", "location__state")
    autocomplete_fields = ("location",)
    date_hierarchy = "time"
    list_select_related = ("location",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "severity_badge",
        "alert_type",
        "location",
        "starts_at",
        "ends_at",
        "is_active",
    )
    list_filter = ("severity", "alert_type", "is_active", "starts_at")
    search_fields = ("title", "areas", "description", "location__name", "location__state")
    autocomplete_fields = ("location",)
    date_hierarchy = "starts_at"
    list_select_related = ("location",)
    actions = ("activate_alerts", "deactivate_alerts")
    fieldsets = (
        ("警報內容", {
            "fields": ("title", "alert_type", "severity", "urgency", "location", "areas")
        }),
        ("時間與狀態", {
            "fields": ("starts_at", "ends_at", "issued_at", "is_active", "source")
        }),
        ("說明", {"fields": ("description", "instruction")}),
    )

    @admin.display(description="嚴重程度", ordering="severity")
    def severity_badge(self, obj):
        colors = {
            "severe": ("#FDE9E7", "#B3251A"),
            "moderate": ("#FDF3E0", "#9A6A05"),
            "minor": ("#E8F1FC", "#0B4EA6"),
        }
        bg, fg = colors.get(obj.severity, ("#EFF3F8", "#3D5266"))
        return format_html(
            '<span style="display:inline-block;padding:2px 9px;border-radius:999px;'
            'background:{};color:{};font-weight:700;">{}</span>',
            bg,
            fg,
            obj.get_severity_display(),
        )

    @admin.action(description="將選取的警報標記為有效")
    def activate_alerts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"已啟用 {updated} 筆警報。")

    @admin.action(description="將選取的警報標記為失效")
    def deactivate_alerts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"已停用 {updated} 筆警報。")


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    verbose_name_plural = "會員設定"


class SkylineUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = (
        "username",
        "email",
        "display_name",
        "is_staff",
        "is_active",
        "last_login",
    )
    list_select_related = ("profile",)

    @admin.display(description="顯示名稱")
    def display_name(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.display_name if profile and profile.display_name else "—"


admin.site.unregister(User)
admin.site.register(User, SkylineUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "home_location",
        "unit",
        "notify_app",
        "notify_email",
        "min_severity",
        "updated_at",
    )
    list_filter = ("unit", "notify_app", "notify_email", "min_severity")
    search_fields = ("user__username", "user__email", "display_name")
    autocomplete_fields = ("user", "home_location")
    list_select_related = ("user", "home_location")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "location__name", "location__state")
    autocomplete_fields = ("user", "location")
    list_select_related = ("user", "location")


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "query", "region", "results_count", "created_at")
    list_filter = ("region", "created_at")
    search_fields = ("user__username", "query")
    autocomplete_fields = ("user",)
    readonly_fields = ("user", "query", "region", "results_count", "created_at")
    list_select_related = ("user",)
