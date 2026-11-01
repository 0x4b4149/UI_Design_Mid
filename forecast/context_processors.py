from django.utils import timezone

from .models import Alert, Profile


def site_context(request):
    profile = None
    if request.user.is_authenticated:
        if not hasattr(request.user, "_cached_profile"):
            request.user._cached_profile, _ = Profile.objects.get_or_create(user=request.user)
        profile = request.user._cached_profile

    unit = request.session.get("unit")
    if unit not in {"f", "c"}:
        if profile and profile.unit in {"f", "c"}:
            unit = profile.unit
        else:
            unit = "f"
        request.session["unit"] = unit

    active_alert_count = 0
    if not request.path.startswith("/admin/"):
        active_alert_count = Alert.objects.filter(
            is_active=True, ends_at__gte=timezone.now()
        ).count()

    return {
        "unit": unit,
        "profile": profile,
        "active_alert_count": active_alert_count,
    }
