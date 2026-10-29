"""前台視圖：三個主要 App 頁面（Home / 7-Day / Alerts）加上會員功能。"""

from django import forms
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Alert, City, DailyForecast, Favorite, MemberProfile

SEV_ORDER = Case(
    When(severity="severe", then=Value(0)),
    When(severity="moderate", then=Value(1)),
    default=Value(2),
    output_field=IntegerField(),
)


def _default_city(request):
    """登入者：第一個收藏城市；訪客：New York（對應 Redesign 首頁在地摘要）。"""
    if request.user.is_authenticated:
        fav = (
            Favorite.objects.filter(user=request.user)
            .select_related("city").first()
        )
        if fav:
            return fav.city
    return City.objects.filter(slug="new-york").first() or City.objects.first()


def home(request):
    q = request.GET.get("q", "").strip()
    results = City.objects.filter(Q(name__icontains=q) | Q(region__icontains=q))[:8] if q else City.objects.none()

    city = _default_city(request)
    today = timezone.localdate()
    today_f = city.forecasts.filter(date=today).first() if city else None

    alerts = Alert.objects.filter(is_active=True).order_by(SEV_ORDER, "starts_at")[:4]
    severe_count = Alert.objects.filter(is_active=True, severity="severe").count()

    favorites = member = None
    if request.user.is_authenticated:
        favorites = (
            Favorite.objects.filter(user=request.user)
            .select_related("city").order_by("created_at")
        )
        member = getattr(request.user, "profile", None)

    return render(request, "home.html", {
        "q": q, "results": results, "city": city, "today_f": today_f,
        "alerts": alerts, "severe_count": severe_count,
        "favorites": favorites, "member": member,
        "searched": bool(q),
    })


def forecast(request, slug):
    city = get_object_or_404(City, slug=slug)
    today = timezone.localdate()
    week = list(city.forecasts.filter(date__gte=today)[:7])

    is_fav = request.user.is_authenticated and Favorite.objects.filter(
        user=request.user, city=city
    ).exists()

    # 決策點：先看週末，否則整週；取降雨機率最低一天當「建議時段」示範
    weekend = [d for d in week if d.is_weekend]
    pool = weekend or week
    best = min(pool, key=lambda d: d.precip_pct) if pool else None

    return render(request, "forecast.html", {
        "city": city, "week": week, "is_fav": is_fav, "best": best,
    })


def alerts(request):
    sev = request.GET.get("severity", "")
    q = request.GET.get("q", "").strip()

    items = Alert.objects.filter(is_active=True)
    if sev in dict(Alert.SEVERITY):
        items = items.filter(severity=sev)
    if q:
        items = items.filter(Q(title__icontains=q) | Q(area__icontains=q))
    items = items.order_by(SEV_ORDER, "starts_at")[:60]

    counts = {
        short: Alert.objects.filter(is_active=True, severity=short).count()
        for short, _label in Alert.SEVERITY
    }
    return render(request, "alerts.html", {
        "items": items, "severity": sev, "q": q, "counts": counts,
    })


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            MemberProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, "註冊完成，已自動登入！")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


class MemberProfileForm(forms.ModelForm):
    class Meta:
        model = MemberProfile
        fields = ["notify_channel", "min_severity"]


@login_required
def profile(request):
    member, _ = MemberProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = MemberProfileForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, "偏好已更新。")
            return redirect("profile")
    else:
        form = MemberProfileForm(instance=member)

    favorites = Favorite.objects.filter(user=request.user).select_related("city")
    return render(request, "profile.html", {
        "form": form, "favorites": favorites, "cities": City.objects.all(),
    })


@login_required
def add_favorite(request):
    """會員中心下拉新增收藏。"""
    if request.method == "POST":
        city_id = request.POST.get("city")
        if city_id and City.objects.filter(pk=city_id).exists():
            fav, created = Favorite.objects.get_or_create(user=request.user, city_id=city_id)
            if created:
                messages.success(request, "已加入收藏。")
            else:
                messages.info(request, "此城市已在收藏中。")
    return redirect("profile")


@login_required
def toggle_favorite(request, city_id):
    """加入 / 移除收藏（登入後才有的操作 → 會員前後差異）。"""
    if request.method == "POST":
        fav, created = Favorite.objects.get_or_create(user=request.user, city_id=city_id)
        if created:
            messages.success(request, "已加入收藏。")
        else:
            fav.delete()
            messages.info(request, "已從收藏移除。")
    return redirect("home")
