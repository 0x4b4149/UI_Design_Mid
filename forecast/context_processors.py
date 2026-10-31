from django.utils import timezone

from .models import Alert, Profile


def site_context(request):
    unit = request.session.get("unit", "f")
    if unit not in {"f", "c"}:
        unit = "f"

    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

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
