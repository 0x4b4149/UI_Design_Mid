from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import connection
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .constants import ALERT_TYPES, CONDITIONS, REGIONS
from .forms import ProfileForm, RegisterForm, StyledAuthenticationForm
from .models import (
    Alert,
    DailyForecast,
    Favorite,
    HourlyForecast,
    Location,
    Profile,
    SearchHistory,
)

SEVERITY_RANK = {"severe": 0, "moderate": 1, "minor": 2}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _favorite_ids(request):
    if not request.user.is_authenticated:
        return set()
    return set(
        Favorite.objects.filter(user=request.user).values_list("location_id", flat=True)
    )


def _active_alerts():
    return Alert.objects.filter(
        is_active=True, ends_at__gte=timezone.now()
    ).select_related("location")


def _sort_alerts(alerts):
    return sorted(alerts, key=lambda item: (item.severity_rank, -item.starts_at.timestamp()))


def _sparkline(values, width=320, height=96, pad=10):
    if not values:
        return ""
    low, high = min(values), max(values)
    span = max(high - low, 1)
    step = (width - pad * 2) / max(len(values) - 1, 1)
    points = []
    for index, value in enumerate(values):
        x = pad + index * step
        y = height - pad - ((value - low) / span) * (height - pad * 2)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def _best_window(hourly):
    """Pick the best three consecutive daylight hours with low rain chance."""
    best, best_score = None, None
    for index in range(len(hourly) - 2):
        chunk = hourly[index : index + 3]
        first, last = chunk[0], chunk[-1]
        if last.time - first.time != timedelta(hours=2):
            continue
        local_hours = [timezone.localtime(hour.time) for hour in chunk]
        if not all(7 <= moment.hour <= 19 for moment in local_hours):
            continue
        if any(hour.precip_percent > 15 for hour in chunk):
            continue
        score = sum(hour.precip_percent for hour in chunk) + abs(local_hours[0].hour - 9)
        if best_score is None or score < best_score:
            best, best_score = chunk, score
    if not best:
        return None
    return (timezone.localtime(best[0].time), timezone.localtime(best[-1].time))


def _insights(current, hourly):
    if not current:
        return []
    items = []
    max_rain = max((hour.precip_percent for hour in hourly), default=0)

    if max_rain >= 50:
        items.append({
            "icon": "umbrella",
            "tone": "warn",
            "title": f"降雨機率高達 {max_rain}%",
            "body": "外出請攜帶雨具，開車留意積水與較長的煞車距離。",
        })
    elif max_rain >= 20:
        items.append({
            "icon": "umbrella",
            "tone": "info",
            "title": f"有短暫陣雨機會（{max_rain}%）",
            "body": "建議在包包放一把折疊傘，較長時間的戶外行程可安排備案。",
        })
    else:
        items.append({
            "icon": "umbrella",
            "tone": "good",
            "title": "未來 12 小時降雨機率低",
            "body": f"最高僅 {max_rain}%，適合安排戶外活動。",
        })

    window = _best_window(hourly)
    if window:
        items.append({
            "icon": "walk",
            "tone": "good",
            "title": "最適合外出的時段",
            "body": (
                f"{window[0]:%H:%M}–{window[1]:%H:%M} 降雨機率低、風勢平穩，"
                "散步或通勤都相對舒適。"
            ),
        })
    else:
        items.append({
            "icon": "walk",
            "tone": "info",
            "title": "戶外活動建議縮短",
            "body": "接下來 12 小時沒有明顯的乾燥空檔，出門記得留意天氣變化。",
        })

    items.append({
        "icon": "air",
        "tone": "good" if current.aqi <= 100 else "warn",
        "title": f"空氣品質 {current.aqi_level}（AQI {current.aqi}）",
        "body": (
            "敏感族群可正常進行戶外活動。"
            if current.aqi <= 100
            else "敏感族群建議減少長時間的戶外劇烈運動。"
        ),
    })

    if current.wind_mph >= 18:
        items.append({
            "icon": "wind",
            "tone": "warn",
            "title": f"風勢偏強（{current.wind_mph} mph）",
            "body": "騎車與高空作業請注意側風，海邊活動留意長浪。",
        })
    return items


def _nearby(location, limit=4):
    queryset = Location.objects.select_related("current").exclude(pk=location.pk)
    same_region = list(queryset.filter(region=location.region)[:limit])
    if len(same_region) < limit:
        extra = list(
            queryset.exclude(pk__in=[item.pk for item in same_region])
            .filter(is_featured=True)[: limit - len(same_region)]
        )
        same_region.extend(extra)
    return same_region


# ---------------------------------------------------------------------------
# public pages
# ---------------------------------------------------------------------------
def home(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    location = None
    if profile and profile.home_location_id:
        location = profile.home_location
    if location is None:
        location = (
            Location.objects.select_related("current").filter(slug="new-york-ny").first()
            or Location.objects.select_related("current").filter(is_featured=True).first()
            or Location.objects.select_related("current").first()
        )
    if location is None:
        return render(request, "empty.html")

    current = getattr(location, "current", None)
    hourly = list(
        HourlyForecast.objects.filter(
            location=location, time__gte=timezone.now() - timedelta(hours=1)
        )[:12]
    )
    if not hourly:
        hourly = list(location.hourly.all()[:12])
    week = list(location.daily.all()[:7])
    alerts = _sort_alerts(
        _active_alerts().filter(location=location)[:6]
    )[:3]
    regional = _nearby(location, limit=4)
    insights = _insights(current, hourly)
    values = [hour.temp_f for hour in hourly]

    context = {
        "location": location,
        "current": current,
        "hourly": hourly,
        "week": week,
        "alerts": alerts,
        "regional": regional,
        "insights": insights,
        "sparkline": _sparkline(values),
        "sparkline_values": values,
        "favorite_ids": _favorite_ids(request),
        "saved": location.pk in _favorite_ids(request),
        "best_window": _best_window(hourly),
        "today": timezone.localdate(),
    }
    return render(request, "home.html", context)


def locations(request):
    q = (request.GET.get("q") or "").strip()
    region = request.GET.get("region", "").strip()
    condition = request.GET.get("condition", "").strip()
    alert_filter = request.GET.get("alerts", "").strip()
    sort = request.GET.get("sort", "name").strip()
    temp_min = _to_int(request.GET.get("temp_min"))
    temp_max = _to_int(request.GET.get("temp_max"))

    queryset = (
        Location.objects.select_related("current")
        .annotate(
            active_alert_count=Count(
                "alerts",
                filter=Q(alerts__is_active=True, alerts__ends_at__gte=timezone.now()),
                distinct=True,
            )
        )
    )

    if q:
        queryset = queryset.filter(
            Q(name__icontains=q)
            | Q(state__icontains=q)
            | Q(county__icontains=q)
            | Q(zip_code__icontains=q)
            | Q(station_code__icontains=q)
        )
    if region:
        queryset = queryset.filter(region=region)
    if condition:
        queryset = queryset.filter(current__condition=condition)
    if temp_min is not None:
        queryset = queryset.filter(current__temp_f__gte=temp_min)
    if temp_max is not None:
        queryset = queryset.filter(current__temp_f__lte=temp_max)
    if alert_filter == "1":
        queryset = queryset.filter(alerts__is_active=True, alerts__ends_at__gte=timezone.now()).distinct()

    sort_map = {
        "name": ("state", "name"),
        "name_desc": ("-state", "-name"),
        "temp_desc": ("-current__temp_f", "name"),
        "temp_asc": ("current__temp_f", "name"),
        "alerts": ("-active_alert_count", "state", "name"),
    }
    queryset = queryset.order_by(*sort_map.get(sort, sort_map["name"]))

    total = queryset.count()
    if request.user.is_authenticated and q:
        last = SearchHistory.objects.filter(user=request.user).first()
        if not last or last.query != q:
            SearchHistory.objects.create(
                user=request.user, query=q, region=region, results_count=total
            )

    from django.core.paginator import Paginator

    paginator = Paginator(queryset, 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)

    context = {
        "page_obj": page_obj,
        "total": total,
        "q": q,
        "selected_region": region,
        "selected_condition": condition,
        "alert_filter": alert_filter,
        "sort": sort,
        "temp_min": temp_min if temp_min is not None else "",
        "temp_max": temp_max if temp_max is not None else "",
        "regions": REGIONS,
        "conditions": CONDITIONS,
        "favorite_ids": _favorite_ids(request),
        "query_without_page": params.urlencode(),
        "has_filters": any([q, region, condition, alert_filter, temp_min, temp_max]),
    }
    return render(request, "locations.html", context)


def location_detail(request, slug):
    location = get_object_or_404(Location.objects.select_related("current"), slug=slug)
    current = getattr(location, "current", None)
    hourly = list(location.hourly.all()[:24])
    week = list(location.daily.all()[:7])
    alerts = _sort_alerts(_active_alerts().filter(location=location))
    insights = _insights(current, hourly[:12])
    values = [hour.temp_f for hour in hourly[:12]]

    context = {
        "location": location,
        "current": current,
        "hourly": hourly,
        "week": week,
        "alerts": alerts,
        "insights": insights,
        "sparkline": _sparkline(values),
        "favorite_ids": _favorite_ids(request),
        "saved": location.pk in _favorite_ids(request),
        "nearby": _nearby(location),
        "best_window": _best_window(hourly),
        "today": timezone.localdate(),
    }
    return render(request, "location_detail.html", context)


def alerts(request):
    base = _active_alerts()
    severity_counts = {
        row["severity"]: row["n"]
        for row in base.values("severity").annotate(n=Count("id"))
    }

    severity = request.GET.get("severity", "").strip()
    alert_type = request.GET.get("type", "").strip()
    region = request.GET.get("region", "").strip()
    q = (request.GET.get("q") or "").strip()

    queryset = base
    if severity:
        queryset = queryset.filter(severity=severity)
    if alert_type:
        queryset = queryset.filter(alert_type=alert_type)
    if region:
        queryset = queryset.filter(location__region=region)
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(areas__icontains=q)
            | Q(location__name__icontains=q)
            | Q(location__state__icontains=q)
        )

    alert_list = _sort_alerts(list(queryset))
    from django.core.paginator import Paginator

    page_obj = Paginator(alert_list, 8).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)

    context = {
        "page_obj": page_obj,
        "total": len(alert_list),
        "severity_counts": severity_counts,
        "selected_severity": severity,
        "selected_type": alert_type,
        "selected_region": region,
        "q": q,
        "types": ALERT_TYPES,
        "regions": REGIONS,
        "query_without_page": params.urlencode(),
        "favorite_ids": _favorite_ids(request),
    }
    return render(request, "alerts.html", context)


def alert_detail(request, pk):
    alert = get_object_or_404(
        Alert.objects.select_related("location"), pk=pk
    )
    related = _sort_alerts(
        _active_alerts()
        .filter(location__region=alert.location.region)
        .exclude(pk=alert.pk)[:4]
    )
    affected = Location.objects.select_related("current").filter(
        pk=alert.location_id
    )

    context = {
        "alert": alert,
        "related": related,
        "affected": affected,
        "saved": alert.location_id in _favorite_ids(request),
        "favorite_ids": _favorite_ids(request),
    }
    return render(request, "alert_detail.html", context)


# ---------------------------------------------------------------------------
# member area
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    favorites = list(
        Favorite.objects.filter(user=request.user).select_related(
            "location", "location__current"
        )
    )
    favorite_locations = [favorite.location for favorite in favorites]
    favorite_ids = {location.pk for location in favorite_locations}

    recent, seen = [], set()
    for entry in request.user.search_history.all()[:30]:
        key = entry.query.lower()
        if key in seen:
            continue
        seen.add(key)
        recent.append(entry)
        if len(recent) == 6:
            break

    my_alerts = _sort_alerts(
        _active_alerts().filter(location__in=favorite_locations)
    )[:4] if favorite_locations else []

    recommended = (
        Location.objects.select_related("current")
        .exclude(pk__in=favorite_ids)
        .filter(is_featured=True)[:3]
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "會員偏好已更新。")
            return redirect("dashboard")
        messages.error(request, "設定未儲存，請檢查欄位內容。")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "profile": profile,
        "favorites": favorites,
        "recent": recent,
        "my_alerts": my_alerts,
        "recommended": recommended,
        "form": form,
        "favorite_ids": favorite_ids,
        "alert_count": _active_alerts().filter(location__in=favorite_locations).count() if favorite_locations else 0,
        "severity_counts": {
            row["severity"]: row["n"]
            for row in _active_alerts()
            .filter(location__in=favorite_locations)
            .values("severity")
            .annotate(n=Count("id"))
        } if favorite_locations else {},
    }
    return render(request, "dashboard.html", context)


@login_required
@require_POST
def toggle_favorite(request, slug):
    location = get_object_or_404(Location, slug=slug)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user, location=location
    )
    if created:
        messages.success(request, f"已將 {location.full_name} 加入收藏。")
    else:
        favorite.delete()
        messages.info(request, f"已從收藏移除 {location.full_name}。")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("home")


def set_unit(request, unit):
    if unit in {"f", "c"}:
        request.session["unit"] = unit
    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("home")


class SkylineLoginView(LoginView):
    template_name = "auth/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "帳號建立成功，歡迎加入 Skyline Weather！")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "auth/register.html", {"form": form})


# ---------------------------------------------------------------------------
# small endpoints
# ---------------------------------------------------------------------------
def search_suggestions(request):
    q = (request.GET.get("q") or "").strip()
    unit = request.session.get("unit", "f")
    if len(q) < 1:
        return JsonResponse({"results": []})

    matches = (
        Location.objects.select_related("current")
        .filter(
            Q(name__icontains=q)
            | Q(state__icontains=q)
            | Q(county__icontains=q)
            | Q(zip_code__icontains=q)
        )
        .order_by("state", "name")[:6]
    )
    results = []
    for location in matches:
        current = getattr(location, "current", None)
        temp_value = None
        if current:
            temp_value = (
                round((current.temp_f - 32) * 5 / 9)
                if unit == "c"
                else current.temp_f
            )
        results.append(
            {
                "name": location.name,
                "state": location.state,
                "label": location.full_name,
                "county": location.county,
                "url": location.get_absolute_url(),
                "temp": temp_value,
                "unit": "°C" if unit == "c" else "°F",
                "condition": current.get_condition_display() if current else "",
            }
        )
    return JsonResponse({"results": results})


def not_found(request, exception):
    return render(request, "404.html", status=404)


def healthz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ok", "database": "up"})
    except Exception:  # pragma: no cover - operational endpoint
        return JsonResponse(
            {"status": "error", "database": "down"}, status=503
        )
