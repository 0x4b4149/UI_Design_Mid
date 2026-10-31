"""Shared choices and labels for the Skyline Weather prototype."""

CONDITIONS = [
    ("sunny", "晴朗"),
    ("mostly_sunny", "晴時多雲"),
    ("partly_cloudy", "多雲時晴"),
    ("cloudy", "多雲"),
    ("showers", "局部陣雨"),
    ("rain", "有雨"),
    ("thunderstorm", "雷雨"),
    ("snow", "下雪"),
    ("fog", "有霧"),
    ("windy", "風大"),
]

REGIONS = [
    ("northeast", "東北部"),
    ("southeast", "東南部"),
    ("midwest", "中西部"),
    ("southwest", "西南部"),
    ("west", "西部"),
]

ALERT_TYPES = [
    ("coastal_flood", "海岸淹水"),
    ("flood", "淹水"),
    ("wind", "強風"),
    ("rip_current", "離岸流"),
    ("winter", "冬季天氣"),
    ("heat", "高溫"),
    ("air_quality", "空氣品質"),
    ("thunderstorm", "雷雨"),
]

SEVERITIES = [
    ("minor", "Minor"),
    ("moderate", "Moderate"),
    ("severe", "Severe"),
]

SEVERITY_LABELS_ZH = {
    "minor": "輕微",
    "moderate": "中等",
    "severe": "嚴重",
}

URGENCIES = [
    ("expected", "Expected"),
    ("immediate", "Immediate"),
    ("future", "Future"),
]

UNITS = [("f", "°F"), ("c", "°C")]

REGION_CENTERS = {
    "northeast": "東北部",
    "southeast": "東南部",
    "midwest": "中西部",
    "southwest": "西南部",
    "west": "西部",
}
