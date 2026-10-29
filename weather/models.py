from django.conf import settings
from django.db import models


class City(models.Model):
    """城市（多元資料管理的主檔）"""

    name = models.CharField("城市", max_length=64)
    slug = models.SlugField("URL 代稱", unique=True)
    region = models.CharField("所屬地區", max_length=64, blank=True)
    lat = models.FloatField("緯度", default=0)
    lon = models.FloatField("經度", default=0)

    class Meta:
        verbose_name = "城市"
        verbose_name_plural = "城市"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.region}"


class DailyForecast(models.Model):
    """七天預報：前台查詢、後台維護的核心資料"""

    CONDITIONS = [
        ("sun", "Sunny"),
        ("cloud", "Cloudy"),
        ("rain", "Rain"),
        ("storm", "Thunderstorms"),
        ("snow", "Snow"),
    ]

    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="forecasts",
        verbose_name="城市",
    )
    date = models.DateField("日期")
    temp_high_c = models.IntegerField("最高溫 (°C)")
    temp_low_c = models.IntegerField("最低溫 (°C)")
    precip_pct = models.IntegerField("降雨機率 (%)", default=0)
    wind_kmh = models.IntegerField("風速 (km/h)", default=0)
    condition = models.CharField("天氣型態", max_length=16, choices=CONDITIONS)
    best_time_hint = models.CharField("最佳時段建議", max_length=48, blank=True)

    class Meta:
        verbose_name = "每日預報"
        verbose_name_plural = "每日預報"
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(fields=["city", "date"], name="uniq_city_date"),
        ]

    def __str__(self):
        return f"{self.city.name} {self.date}"

    @property
    def is_weekend(self):
        return self.date.weekday() >= 5  # 6=週六, 0=週一 → 5,6 為週末

    @property
    def condition_icon(self):
        return {
            "sun": "☀️", "cloud": "⛅", "rain": "🌧️",
            "storm": "⛈️", "snow": "❄️",
        }.get(self.condition, "")


class Alert(models.Model):
    """氣象警報：嚴重度、影響範圍、生效時間與建議行動"""

    SEVERITY = [
        ("severe", "Severe"),
        ("moderate", "Moderate"),
        ("minor", "Minor"),
    ]

    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="alerts", verbose_name="相關城市（留空＝全國）",
    )
    title = models.CharField("警報名稱", max_length=128)
    severity = models.CharField("嚴重度", max_length=16, choices=SEVERITY)
    area = models.CharField("影響地區", max_length=128, default="")
    starts_at = models.DateTimeField("生效開始")
    ends_at = models.DateTimeField("結束時間")
    advice = models.TextField("官方建議行動", blank=True)
    is_active = models.BooleanField("生效中", default=True)

    class Meta:
        verbose_name = "警報"
        verbose_name_plural = "警報"

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"


class Favorite(models.Model):
    """會員收藏城市 → 登入前後介面差異的核心功能"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="favorites", verbose_name="會員",
    )
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="favorited_by",
        verbose_name="城市",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "收藏城市"
        verbose_name_plural = "收藏城市"
        constraints = [
            models.UniqueConstraint(fields=["user", "city"], name="uniq_user_city"),
        ]

    def __str__(self):
        return f"{self.user} → {self.city}"


class MemberProfile(models.Model):
    """會員偏好：通知渠道與警報嚴重度門檻"""

    CHANNELS = [
        ("dashboard", "網站通知"),
        ("email", "Email 通知"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="profile", verbose_name="會員",
    )
    notify_channel = models.CharField(
        "通知渠道", max_length=16, choices=CHANNELS, default="dashboard",
    )
    min_severity = models.CharField(
        "通知門檻（嚴重度以上）", max_length=16,
        choices=Alert.SEVERITY, default="minor",
    )

    class Meta:
        verbose_name = "會員偏好"
        verbose_name_plural = "會員偏好"

    def __str__(self):
        return f"{self.user} 偏好"
