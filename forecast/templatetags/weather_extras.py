from zoneinfo import ZoneInfo

from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe

from ..constants import CONDITIONS, SEVERITY_LABELS_ZH

register = template.Library()

CONDITION_LABELS = dict(CONDITIONS)

RAIN = "#3D8BDA"
CLOUD_FILL = "#EDF3FA"
CLOUD_LINE = "#93AEC8"
SUN = "#F5B23C"
SUN_RAY = "#E8A02B"
SNOW = "#7FB7E8"

SUN_CORE = f'<circle cx="32" cy="30" r="10" fill="{SUN}"/>'

SUN_RAYS = (
    f'<g stroke="{SUN_RAY}" stroke-width="3" stroke-linecap="round">'
    '<path d="M32 8v6M32 46v6M10 30h6M48 30h6'
    'M16.5 14.5l4.2 4.2M43.3 41.3l4.2 4.2M47.5 14.5l-4.2 4.2M20.7 41.3l-4.2 4.2"/>'
    "</g>"
)

CLOUD = (
    f'<path d="M18 45h27a9 9 0 0 0 1.4-17.9A14 14 0 0 0 20.6 31 8 8 0 0 0 18 45Z" '
    f'fill="{CLOUD_FILL}" stroke="{CLOUD_LINE}" stroke-width="2.4" stroke-linejoin="round"/>'
)

SMALL_CLOUD = (
    f'<path d="M24 44h24a8 8 0 0 0 1.2-15.9A12 12 0 0 0 26.4 31 7 7 0 0 0 24 44Z" '
    f'fill="{CLOUD_FILL}" stroke="{CLOUD_LINE}" stroke-width="2.4" stroke-linejoin="round"/>'
)


def _sunny():
    return SUN_RAYS + SUN_CORE


def _mostly_sunny():
    return (
        SUN_RAYS
        + SUN_CORE
        + '<path d="M22 46h26a8 8 0 0 0 1-15.9A12 12 0 0 0 26 32a7 7 0 0 0-4 14Z" '
        f'fill="{CLOUD_FILL}" stroke="{CLOUD_LINE}" stroke-width="2.4" stroke-linejoin="round"/>'
    )


def _partly_cloudy():
    return (
        '<g opacity=".95">'
        f'<g stroke="{SUN_RAY}" stroke-width="2.6" stroke-linecap="round">'
        '<path d="M24 10v5M10 24h5M14 14l3.5 3.5M34 14l-3.5 3.5"/></g>'
        f'<circle cx="24" cy="24" r="7.5" fill="{SUN}"/></g>'
        + SMALL_CLOUD
    )


def _cloudy():
    return (
        f'<path d="M20 39h25a8 8 0 0 0 1-15.8A13 13 0 0 0 22.5 26 7 7 0 0 0 20 39Z" '
        f'fill="#DEE8F3" stroke="{CLOUD_LINE}" stroke-width="2.2" stroke-linejoin="round"/>'
        + CLOUD
    )


def _rain(drops=3):
    lines = "".join(
        f'<path d="M{x} {y}l-2 7" stroke="{RAIN}" stroke-width="3" stroke-linecap="round"/>'
        for x, y in [(20, 49), (29, 49), (38, 49), (47, 49)][:drops]
    )
    return CLOUD + lines


def _showers():
    return _rain(3)


def _rainy():
    return _rain(4)


def _thunderstorm():
    return (
        f'<path d="M18 41h27a9 9 0 0 0 1.4-17.9A14 14 0 0 0 20.6 27 8 8 0 0 0 18 41Z" '
        f'fill="#C9D6E4" stroke="#7D93AA" stroke-width="2.4" stroke-linejoin="round"/>'
        '<polygon points="34,39 25,52 32,52 29,62 42,47 34,47" fill="#F5B23C" stroke="#D9941E" stroke-width="1.2"/>'
    )


def _snow():
    flakes = []
    for cx, cy in [(24, 52), (34, 55), (44, 52)]:
        flakes.append(
            f'<g stroke="{SNOW}" stroke-width="2" stroke-linecap="round">'
            f'<path d="M{cx-4} {cy}h8M{cx} {cy-4}v8M{cx-3} {cy-3}l6 6M{cx+3} {cy-3}l-6 6"/></g>'
        )
    return CLOUD + "".join(flakes)


def _fog():
    return (
        CLOUD
        + f'<g stroke="#9DB4CC" stroke-width="2.6" stroke-linecap="round">'
        '<path d="M16 51h32M22 57h26M14 57h4"/></g>'
    )


def _windy():
    return (
        '<g fill="none" stroke="#7FA6C9" stroke-width="3" stroke-linecap="round">'
        '<path d="M9 24h27a5 5 0 1 0-5-5"/>'
        '<path d="M9 35h36a5 5 0 1 1-5 5"/>'
        '<path d="M9 46h21a4 4 0 1 1-4 4"/>'
        "</g>"
        f'<circle cx="45" cy="18" r="3" fill="{SUN}"/>'
    )


ICON_BODIES = {
    "sunny": _sunny,
    "mostly_sunny": _mostly_sunny,
    "partly_cloudy": _partly_cloudy,
    "cloudy": _cloudy,
    "showers": _showers,
    "rain": _rainy,
    "thunderstorm": _thunderstorm,
    "snow": _snow,
    "fog": _fog,
    "windy": _windy,
}


@register.simple_tag
def weather_icon(condition, size=48, css_class=""):
    body = ICON_BODIES.get(condition, _cloudy)()
    label = CONDITION_LABELS.get(condition, "天氣")
    return mark_safe(
        f'<svg class="weather-icon {css_class}" width="{size}" height="{size}" '
        'viewBox="0 0 64 64" fill="none" role="img" aria-label="'
        + label
        + '">'
        + f"<title>{label}</title>"
        + body
        + "</svg>"
    )


@register.simple_tag
def ui_icon(name, size=20, css_class=""):
    return mark_safe(
        f'<svg class="icon {css_class}" width="{size}" height="{size}" '
        f'aria-hidden="true"><use href="#i-{name}"></use></svg>'
    )


@register.filter
def temp(value, unit="f"):
    if value is None or value == "":
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"
    if unit == "c":
        value = (value - 32) * 5 / 9
    return f"{round(value)}°"


@register.filter
def temp_full(value, unit="f"):
    if value is None or value == "":
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"
    if unit == "c":
        return f"{round((value - 32) * 5 / 9)}°C"
    return f"{round(value)}°F"


@register.filter
def in_tz(value, tzname):
    if not value or not tzname:
        return value
    try:
        return timezone.localtime(value, ZoneInfo(tzname))
    except (ValueError, KeyError, TypeError):
        return value


@register.filter
def hour_label(value):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value, timezone=value.tzinfo)
    return value.strftime("%I%p").lstrip("0")


@register.filter
def day_label(value):
    if not value:
        return ""
    return ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][value.weekday()]


@register.filter
def date_short(value):
    if not value:
        return ""
    return value.strftime("%m/%d")


@register.filter
def time_short(value):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%H:%M")


@register.filter
def severity_zh(value):
    return SEVERITY_LABELS_ZH.get(value, value)


@register.filter
def severity_class(value):
    return {"severe": "sev", "moderate": "mod", "minor": "min"}.get(value, "min")


ALERT_ICONS = {
    "coastal_flood": "wave",
    "flood": "wave",
    "wind": "wind",
    "rip_current": "wave",
    "winter": "snowflake",
    "heat": "thermometer",
    "air_quality": "air",
    "thunderstorm": "zap",
}


@register.filter
def alert_icon(value):
    return ALERT_ICONS.get(value, "alert")


@register.filter
def initials(value):
    value = (value or "").strip()
    if not value:
        return "U"
    return value[:1].upper()


@register.filter
def get_item(mapping, key):
    if hasattr(mapping, "get"):
        return mapping.get(key)
    return None


@register.filter
def absval(value):
    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return value


@register.filter
def divide(value, arg):
    try:
        return round(float(value) / float(arg))
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
