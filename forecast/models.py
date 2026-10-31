from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .constants import ALERT_TYPES, CONDITIONS, REGIONS, SEVERITIES, UNITS, URGENCIES


class Location(models.Model):
    name = models.CharField("城市", max_length=80)
    state = models.CharField("州別", max_length=2)
    slug = models.SlugField("網址代稱", max_length=120, unique=True)
    county = models.CharField("郡 / 行政區", max_length=100, blank=True)
    zip_code = models.CharField("郵遞區號", max_length=12, blank=True)
    region = models.CharField("區域", max_length=20, choices=REGIONS, default="northeast")
    latitude = models.DecimalField("緯度", max_digits=9, decimal_places=6)
    longitude = models.DecimalField("經度", max_digits=9, decimal_places=6)
    timezone = models.CharField("時區", max_length=64, default="America/New_York")
    station_code = models.CharField("測站代碼", max_length=12, blank=True)
    elevation_ft = models.PositiveIntegerField("海拔（英尺）", default=0)
    description = models.TextField("城市簡介", blank=True)
    is_featured = models.BooleanField("首頁精選", default=False)
    created_at = models.DateTimeField("建立時間", auto_now_add=True)

    class Meta:
        verbose_name = "城市"
        verbose_name_plural = "城市"
        ordering = ["state", "name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["state"]),
            models.Index(fields=["region"]),
        ]

    def __str__(self):
        return f"{self.name}, {self.state}"

    @property
    def full_name(self):
        return f"{self.name}, {self.state}"

    def get_absolute_url(self):
        return reverse("location_detail", kwargs={"slug": self.slug})

    @property
    def current_temp(self):
        current = getattr(self, "current", None)
        return current.temp_f if current else None

    @property
    def condition_label(self):
        current = getattr(self, "current", None)
        return current.get_condition_display() if current else "尚無觀測"


class CurrentConditions(models.Model):
    location = models.OneToOneField(
        Location, on_delete=models.CASCADE, related_name="current", verbose_name="城市"
    )
    temp_f = models.IntegerField("現在溫度（°F）")
    feels_like_f = models.IntegerField("體感溫度（°F）")
    condition = models.CharField("天氣狀況", max_length=24, choices=CONDITIONS)
    humidity = models.PositiveSmallIntegerField("濕度（%）", default=50)
    wind_direction = models.CharField("風向", max_length=8, default="N")
    wind_mph = models.PositiveSmallIntegerField("風速（mph）", default=0)
    gust_mph = models.PositiveSmallIntegerField("陣風（mph）", default=0)
    visibility_mi = models.DecimalField(
        "能見度（英里）", max_digits=4, decimal_places=1, default=10
    )
    pressure_in = models.DecimalField(
        "氣壓（inHg）", max_digits=5, decimal_places=2, default=30.00
    )
    dew_point_f = models.IntegerField("露點（°F）", default=45)
    uv_index = models.PositiveSmallIntegerField("紫外線指數", default=3)
    aqi = models.PositiveSmallIntegerField("空氣品質指數 AQI", default=35)
    high_f = models.IntegerField("今日最高溫（°F）")
    low_f = models.IntegerField("今日最低溫（°F）")
    summary = models.TextField("觀測摘要", blank=True)
    observed_at = models.DateTimeField("觀測時間", default=timezone.now)

    class Meta:
        verbose_name = "即時觀測"
        verbose_name_plural = "即時觀測"

    def __str__(self):
        return f"{self.location} · {self.temp_f}°F"

    @property
    def aqi_level(self):
        if self.aqi <= 50:
            return "良好"
        if self.aqi <= 100:
            return "普通"
        if self.aqi <= 150:
            return "對敏感族群不健康"
        return "不健康"

    @property
    def uv_level(self):
        if self.uv_index <= 2:
            return "低"
        if self.uv_index <= 5:
            return "中等"
        if self.uv_index <= 7:
            return "高"
        return "非常高"


class DailyForecast(models.Model):
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="daily", verbose_name="城市"
    )
    date = models.DateField("日期")
    condition = models.CharField("天氣狀況", max_length=24, choices=CONDITIONS)
    high_f = models.IntegerField("最高溫（°F）")
    low_f = models.IntegerField("最低溫（°F）")
    precip_percent = models.PositiveSmallIntegerField("降雨機率（%）", default=0)
    wind = models.CharField("風勢", max_length=40, blank=True)
    summary = models.CharField("天氣摘要", max_length=160, blank=True)
    sunrise = models.TimeField("日出", null=True, blank=True)
    sunset = models.TimeField("日落", null=True, blank=True)

    class Meta:
        verbose_name = "每日預報"
        verbose_name_plural = "每日預報"
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["location", "date"], name="unique_daily_location_date"
            )
        ]

    def __str__(self):
        return f"{self.location} · {self.date}"

    @property
    def is_weekend(self):
        return self.date.weekday() >= 5


class HourlyForecast(models.Model):
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="hourly", verbose_name="城市"
    )
    time = models.DateTimeField("時間")
    temp_f = models.IntegerField("溫度（°F）")
    condition = models.CharField("天氣狀況", max_length=24, choices=CONDITIONS)
    precip_percent = models.PositiveSmallIntegerField("降雨機率（%）", default=0)
    wind_mph = models.PositiveSmallIntegerField("風速（mph）", default=0)
    summary = models.CharField("摘要", max_length=120, blank=True)

    class Meta:
        verbose_name = "逐時預報"
        verbose_name_plural = "逐時預報"
        ordering = ["time"]
        constraints = [
            models.UniqueConstraint(
                fields=["location", "time"], name="unique_hourly_location_time"
            )
        ]

    def __str__(self):
        return f"{self.location} · {self.time:%m/%d %H:%M}"


class Alert(models.Model):
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="alerts", verbose_name="主要影響城市"
    )
    title = models.CharField("警報標題", max_length=160)
    alert_type = models.CharField("警報類型", max_length=24, choices=ALERT_TYPES)
    severity = models.CharField("嚴重程度", max_length=12, choices=SEVERITIES)
    urgency = models.CharField("緊急程度", max_length=12, choices=URGENCIES, default="expected")
    areas = models.CharField("影響區域", max_length=200)
    description = models.TextField("警報說明")
    instruction = models.TextField("建議行動", blank=True)
    starts_at = models.DateTimeField("開始時間")
    ends_at = models.DateTimeField("結束時間")
    issued_at = models.DateTimeField("發布時間", default=timezone.now)
    source = models.CharField("資料來源", max_length=80, default="NWS")
    is_active = models.BooleanField("有效中", default=True)
    created_at = models.DateTimeField("建立時間", auto_now_add=True)

    class Meta:
        verbose_name = "天氣警報"
        verbose_name_plural = "天氣警報"
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["severity", "is_active"]),
            models.Index(fields=["alert_type"]),
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"

    def get_absolute_url(self):
        return reverse("alert_detail", kwargs={"pk": self.pk})

    @property
    def severity_rank(self):
        return {"severe": 0, "moderate": 1, "minor": 2}.get(self.severity, 3)

    @property
    def is_expired(self):
        return self.ends_at < timezone.now()

    @property
    def duration_label(self):
        start = timezone.localtime(self.starts_at)
        end = timezone.localtime(self.ends_at)
        if start.date() == end.date():
            return f"{start:%m/%d %H:%M} – {end:%H:%M}"
        return f"{start:%m/%d %H:%M} – {end:%m/%d %H:%M}"

    @property
    def instruction_list(self):
        return [line.strip("-• ").strip() for line in self.instruction.splitlines() if line.strip()]


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorites", verbose_name="會員"
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="favorited_by", verbose_name="城市"
    )
    created_at = models.DateTimeField("加入時間", auto_now_add=True)

    class Meta:
        verbose_name = "收藏城市"
        verbose_name_plural = "收藏城市"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "location"], name="unique_favorite_user_location"
            )
        ]

    def __str__(self):
        return f"{self.user.username} ♥ {self.location}"


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="會員"
    )
    display_name = models.CharField("顯示名稱", max_length=60, blank=True)
    unit = models.CharField("溫度單位", max_length=1, choices=UNITS, default="f")
    home_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="residents",
        verbose_name="預設城市",
    )
    notify_app = models.BooleanField("App 推播", default=True)
    notify_email = models.BooleanField("Email 通知", default=False)
    notify_sms = models.BooleanField("簡訊通知", default=False)
    min_severity = models.CharField(
        "通知門檻", max_length=12, choices=SEVERITIES, default="moderate"
    )
    updated_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        verbose_name = "會員設定"
        verbose_name_plural = "會員設定"

    def __str__(self):
        return f"{self.user.username} 的偏好設定"

    @property
    def name(self):
        return self.display_name or self.user.get_full_name() or self.user.username


class SearchHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="search_history", verbose_name="會員"
    )
    query = models.CharField("查詢關鍵字", max_length=120)
    region = models.CharField("區域篩選", max_length=20, blank=True)
    results_count = models.PositiveIntegerField("結果數", default=0)
    created_at = models.DateTimeField("查詢時間", auto_now_add=True)

    class Meta:
        verbose_name = "查詢紀錄"
        verbose_name_plural = "查詢紀錄"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} · {self.query}"


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
