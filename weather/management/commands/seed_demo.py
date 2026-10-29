"""建立教學用示範資料：6 城市 × 7 天預報、4 則警報、1 個測試會員。

用法：
  python manage.py seed_demo          # 不覆蓋既存資料
  python manage.py seed_demo --flush  # 先清空再重建
"""
import datetime as dt
import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from weather.models import Alert, City, DailyForecast, Favorite, MemberProfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CITIES = [
    ("new-york", "New York", "New York", 40.71, -74.01, 19),
    ("los-angeles", "Los Angeles", "California", 34.05, -118.24, 24),
    ("chicago", "Chicago", "Illinois", 41.88, -87.63, 6),
    ("miami", "Miami", "Florida", 25.76, -80.19, 30),
    ("seattle", "Seattle", "Washington", 47.61, -122.33, 14),
    ("denver", "Denver", "Colorado", 39.74, -104.99, 12),
]

CONDITIONS = ["sun", "sun", "cloud", "rain", "cloud", "storm", "sun"]
PRECIP = [5, 10, 30, 65, 40, 80, 10]
WIND = [8, 12, 18, 27, 22, 34, 10]

SLUGS = {c[0] for c in CITIES}


class Command(BaseCommand):
    help = "產生示範資料（城市／預報／警報／測試會員）"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true",
                            help="先刪除示範資料再重建")

    def handle(self, *args, **options):
        if options.get("flush"):
            DailyForecast.objects.all().delete()
            Alert.objects.all().delete()
            Favorite.objects.all().delete()
            City.objects.all().delete()
            self.stdout.write(self.style.WARNING("已清空示範資料"))

        if not City.objects.exists():
            for idx, (slug, name, region, lat, lon, base_high) in enumerate(CITIES):
                city = City.objects.create(
                    name=name, slug=slug, region=region, lat=lat, lon=lon,
                )
                start = timezone.localdate()
                for i in range(7):
                    day = start + dt.timedelta(days=i)
                    high = base_high + [0, 1, -2, -4, -1, -6, 2][i]
                    precip = PRECIP[(i + idx * 2) % 7]
                    if precip <= 20:
                        hint = "上午 06:00–11:00"
                    elif precip <= 55:
                        hint = "午後 13:00–16:00"
                    else:
                        hint = "全天不建議戶外活動"
                    DailyForecast.objects.create(
                        city=city, date=day,
                        temp_high_c=high, temp_low_c=high - 8,
                        precip_pct=precip, wind_kmh=WIND[(i + 3) % 7],
                        condition=CONDITIONS[(i + 2) % 7],
                        best_time_hint=hint,
                    )
            self.stdout.write(self.style.SUCCESS("已建立 6 個城市 × 7 天預報"))

        if not Alert.objects.exists():
            now = timezone.now()
            ny = City.objects.filter(slug="new-york").first()
            mi = City.objects.filter(slug="miami").first()
            de = City.objects.filter(slug="denver").first()
            Alert.objects.create(
                city=ny, title="Coastal Flood Warning", severity="severe",
                area="New York City Metro",
                starts_at=now + dt.timedelta(hours=2),
                ends_at=now + dt.timedelta(days=2),
                advice="1. 遠離海岸低窪地區\n2. 避免前往地下捷運站\n3. 收聽市府應變廣播",
            )
            Alert.objects.create(
                city=mi, title="High Surf Advisory", severity="moderate",
                area="Coastal Miami-Dade",
                starts_at=now, ends_at=now + dt.timedelta(days=3),
                advice="1. 海象不佳，勿從事水上活動\n2. 已豎立警告旗幟時勿下海\n3. 留意沿岸交通訊息",
            )
            Alert.objects.create(
                city=de, title="Freeze Watch", severity="minor",
                area="Denver Metro",
                starts_at=now + dt.timedelta(days=1),
                ends_at=now + dt.timedelta(days=3),
                advice="1. 覆蓋戶外植物\n2. 保護水管防凍裂\n3. 準備保暖衣物",
            )
            self.stdout.write(self.style.SUCCESS("已建立 3 則示範警報"))

        if not User.objects.filter(username="demo").exists():
            user = User.objects.create_user(
                username="demo", email="demo@example.com", password="Demo1234!",
                first_name="", last_name="",
            )
            MemberProfile.objects.create(user=user)
            ny = City.objects.filter(slug="new-york").first()
            mi = City.objects.filter(slug="miami").first()
            if ny:
                Favorite.objects.create(user=user, city=ny)
            if mi:
                Favorite.objects.create(user=user, city=mi)
            self.stdout.write(self.style.SUCCESS("已建立測試會員 demo / Demo1234!（收藏 New York、Miami）"))
        else:
            self.stdout.write("測試會員 demo 已存在，略過")
