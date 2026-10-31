"""Seed the Skyline Weather prototype with realistic demo data.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --if-empty

The command is idempotent: locations are updated by slug, forecasts are
rebuilt for the current week, and demo accounts keep a known password.
"""

import math
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from forecast.models import (
    Alert,
    CurrentConditions,
    DailyForecast,
    Favorite,
    HourlyForecast,
    Location,
    Profile,
    SearchHistory,
)

CONDITION_TEXT = {
    "sunny": "晴朗穩定，日照充足。",
    "mostly_sunny": "晴時多雲，適合戶外活動。",
    "partly_cloudy": "雲量偏多，仍有陽光空檔。",
    "cloudy": "多雲，體感偏涼。",
    "showers": "局部陣雨，外出建議帶傘。",
    "rain": "持續降雨，留意積水與濕滑路面。",
    "thunderstorm": "午後雷雨機會高，避免停留在空曠處。",
    "snow": "有降雪機會，注意路面結冰。",
    "fog": "晨間有霧，能見度偏低。",
    "windy": "風勢偏強，騎車與高空作業注意側風。",
}

PRECIP = {
    "sunny": 0,
    "mostly_sunny": 5,
    "partly_cloudy": 10,
    "cloudy": 20,
    "windy": 15,
    "fog": 10,
    "showers": 55,
    "rain": 80,
    "thunderstorm": 75,
    "snow": 65,
}

NIGHT_CONDITION = {
    "sunny": "partly_cloudy",
    "mostly_sunny": "partly_cloudy",
    "partly_cloudy": "cloudy",
    "fog": "fog",
}

LOCATIONS = [
    {
        "name": "New York",
        "state": "NY",
        "slug": "new-york-ny",
        "county": "New York County",
        "zip_code": "10001",
        "region": "northeast",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
        "station_code": "KNYC",
        "elevation_ft": 33,
        "is_featured": True,
        "description": "中央公園測站一帶的天氣代表紐約市，四季分明，秋末常見涼爽的西北風與短暫陣雨。",
        "temp": 58,
        "feels": 56,
        "condition": "partly_cloudy",
        "high": 61,
        "low": 48,
        "humidity": 58,
        "wind_dir": "NW",
        "wind": 8,
        "gust": 16,
        "visibility": "10.0",
        "pressure": "30.12",
        "dew": 43,
        "uv": 3,
        "aqi": 32,
        "summary": "雲量時多時少，下午有陽光空檔；入夜後明顯轉涼。",
        "week": ["partly_cloudy", "mostly_sunny", "sunny", "showers", "cloudy", "partly_cloudy", "mostly_sunny"],
    },
    {
        "name": "Boston",
        "state": "MA",
        "slug": "boston-ma",
        "county": "Suffolk County",
        "zip_code": "02108",
        "region": "northeast",
        "latitude": 42.3601,
        "longitude": -71.0589,
        "timezone": "America/New_York",
        "station_code": "KBOS",
        "elevation_ft": 141,
        "is_featured": False,
        "description": "海港城市，秋季風勢明顯，早晚溫差大，沿海地區偶有強風特報。",
        "temp": 54,
        "feels": 51,
        "condition": "mostly_sunny",
        "high": 58,
        "low": 45,
        "humidity": 61,
        "wind_dir": "W",
        "wind": 11,
        "gust": 21,
        "visibility": "10.0",
        "pressure": "30.05",
        "dew": 41,
        "uv": 3,
        "aqi": 28,
        "summary": "陽光露臉但風偏涼，海邊體感更低，晚間留意低溫。",
        "week": ["mostly_sunny", "sunny", "partly_cloudy", "rain", "cloudy", "showers", "mostly_sunny"],
    },
    {
        "name": "Los Angeles",
        "state": "CA",
        "slug": "los-angeles-ca",
        "county": "Los Angeles County",
        "zip_code": "90012",
        "region": "west",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "timezone": "America/Los_Angeles",
        "station_code": "KLAX",
        "elevation_ft": 285,
        "is_featured": True,
        "description": "地中海型氣候，秋季乾燥晴朗，午後海風明顯；盆地與海邊溫差可達 10°F。",
        "temp": 74,
        "feels": 74,
        "condition": "sunny",
        "high": 79,
        "low": 60,
        "humidity": 42,
        "wind_dir": "SW",
        "wind": 7,
        "gust": 13,
        "visibility": "10.0",
        "pressure": "29.98",
        "dew": 49,
        "uv": 5,
        "aqi": 58,
        "summary": "晴朗乾燥，午後紫外線偏強；沿海地區有局部海風。",
        "week": ["sunny", "sunny", "mostly_sunny", "sunny", "partly_cloudy", "sunny", "sunny"],
    },
    {
        "name": "San Francisco",
        "state": "CA",
        "slug": "san-francisco-ca",
        "county": "San Francisco County",
        "zip_code": "94102",
        "region": "west",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timezone": "America/Los_Angeles",
        "station_code": "KSFO",
        "elevation_ft": 52,
        "is_featured": True,
        "description": "典型海霧城市，同日不同街區可能出現明顯溫差，午後西風強。",
        "temp": 62,
        "feels": 60,
        "condition": "fog",
        "high": 66,
        "low": 54,
        "humidity": 78,
        "wind_dir": "W",
        "wind": 12,
        "gust": 23,
        "visibility": "4.0",
        "pressure": "30.01",
        "dew": 53,
        "uv": 2,
        "aqi": 34,
        "summary": "晨間海霧籠罩，午後逐步消散；西側街區體感偏涼。",
        "week": ["fog", "partly_cloudy", "sunny", "sunny", "fog", "partly_cloudy", "sunny"],
    },
    {
        "name": "Seattle",
        "state": "WA",
        "slug": "seattle-wa",
        "county": "King County",
        "zip_code": "98101",
        "region": "west",
        "latitude": 47.6062,
        "longitude": -122.3321,
        "timezone": "America/Los_Angeles",
        "station_code": "KSEA",
        "elevation_ft": 187,
        "is_featured": False,
        "description": "秋冬季節以層雲與持續性降雨為主，山區與市區天氣差異大。",
        "temp": 54,
        "feels": 51,
        "condition": "rain",
        "high": 57,
        "low": 47,
        "humidity": 86,
        "wind_dir": "S",
        "wind": 9,
        "gust": 18,
        "visibility": "6.0",
        "pressure": "29.86",
        "dew": 50,
        "uv": 1,
        "aqi": 19,
        "summary": "間歇性降雨，山區雨勢較明顯；外出務必攜帶雨具。",
        "week": ["rain", "showers", "cloudy", "partly_cloudy", "showers", "rain", "cloudy"],
    },
    {
        "name": "Chicago",
        "state": "IL",
        "slug": "chicago-il",
        "county": "Cook County",
        "zip_code": "60601",
        "region": "midwest",
        "latitude": 41.8781,
        "longitude": -87.6298,
        "timezone": "America/Chicago",
        "station_code": "KORD",
        "elevation_ft": 594,
        "is_featured": True,
        "description": "風城名不虛傳，秋季冷鋒通過時風勢與降溫都相當明顯。",
        "temp": 50,
        "feels": 45,
        "condition": "windy",
        "high": 53,
        "low": 42,
        "humidity": 63,
        "wind_dir": "W",
        "wind": 19,
        "gust": 31,
        "visibility": "10.0",
        "pressure": "29.92",
        "dew": 38,
        "uv": 2,
        "aqi": 41,
        "summary": "冷鋒過後風勢偏強，湖邊體感更冷；晚間氣溫快速下降。",
        "week": ["windy", "partly_cloudy", "showers", "rain", "cloudy", "mostly_sunny", "partly_cloudy"],
    },
    {
        "name": "Denver",
        "state": "CO",
        "slug": "denver-co",
        "county": "Denver County",
        "zip_code": "80202",
        "region": "southwest",
        "latitude": 39.7392,
        "longitude": -104.9903,
        "timezone": "America/Denver",
        "station_code": "KDEN",
        "elevation_ft": 5280,
        "is_featured": False,
        "description": "高海拔城市，日夜溫差大，秋季第一場雪可能在十月下旬出現。",
        "temp": 55,
        "feels": 52,
        "condition": "mostly_sunny",
        "high": 62,
        "low": 35,
        "humidity": 38,
        "wind_dir": "SW",
        "wind": 8,
        "gust": 17,
        "visibility": "10.0",
        "pressure": "30.08",
        "dew": 27,
        "uv": 4,
        "aqi": 39,
        "summary": "白天晴朗，日落後氣溫驟降；本週後段有降雪機會。",
        "week": ["mostly_sunny", "sunny", "snow", "cloudy", "partly_cloudy", "sunny", "mostly_sunny"],
    },
    {
        "name": "Austin",
        "state": "TX",
        "slug": "austin-tx",
        "county": "Travis County",
        "zip_code": "78701",
        "region": "southwest",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "timezone": "America/Chicago",
        "station_code": "KAUS",
        "elevation_ft": 542,
        "is_featured": False,
        "description": "秋末仍偏暖，午後對流旺盛時容易出現雷陣雨。",
        "temp": 80,
        "feels": 82,
        "condition": "sunny",
        "high": 86,
        "low": 67,
        "humidity": 54,
        "wind_dir": "SE",
        "wind": 6,
        "gust": 12,
        "visibility": "10.0",
        "pressure": "29.94",
        "dew": 62,
        "uv": 6,
        "aqi": 44,
        "summary": "上午晴朗偏熱，午後山區與西側有局部雷陣雨機會。",
        "week": ["sunny", "mostly_sunny", "partly_cloudy", "sunny", "thunderstorm", "showers", "mostly_sunny"],
    },
    {
        "name": "Miami",
        "state": "FL",
        "slug": "miami-fl",
        "county": "Miami-Dade County",
        "zip_code": "33130",
        "region": "southeast",
        "latitude": 25.7617,
        "longitude": -80.1918,
        "timezone": "America/New_York",
        "station_code": "KMIA",
        "elevation_ft": 6,
        "is_featured": True,
        "description": "熱帶氣候，午後雷雨與高濕度是日常；沿海需留意離岸流。",
        "temp": 83,
        "feels": 88,
        "condition": "thunderstorm",
        "high": 87,
        "low": 76,
        "humidity": 74,
        "wind_dir": "E",
        "wind": 10,
        "gust": 22,
        "visibility": "8.0",
        "pressure": "29.99",
        "dew": 74,
        "uv": 6,
        "aqi": 36,
        "summary": "上午悶熱，午後有雷陣雨；海邊留意離岸流與長浪。",
        "week": ["thunderstorm", "showers", "partly_cloudy", "thunderstorm", "sunny", "showers", "partly_cloudy"],
    },
    {
        "name": "New Orleans",
        "state": "LA",
        "slug": "new-orleans-la",
        "county": "Orleans Parish",
        "zip_code": "70112",
        "region": "southeast",
        "latitude": 29.9511,
        "longitude": -90.0715,
        "timezone": "America/Chicago",
        "station_code": "KMSY",
        "elevation_ft": 3,
        "is_featured": False,
        "description": "低窪地形與高濕度讓降雨與淹水風險成為秋季關注焦點。",
        "temp": 78,
        "feels": 82,
        "condition": "showers",
        "high": 82,
        "low": 69,
        "humidity": 79,
        "wind_dir": "SE",
        "wind": 8,
        "gust": 17,
        "visibility": "7.0",
        "pressure": "29.97",
        "dew": 71,
        "uv": 4,
        "aqi": 31,
        "summary": "間歇陣雨，低窪地區留意短時積水；濕度高、體感偏悶。",
        "week": ["showers", "thunderstorm", "cloudy", "partly_cloudy", "sunny", "showers", "mostly_sunny"],
    },
    {
        "name": "Portland",
        "state": "OR",
        "slug": "portland-or",
        "county": "Multnomah County",
        "zip_code": "97205",
        "region": "west",
        "latitude": 45.5152,
        "longitude": -122.6784,
        "timezone": "America/Los_Angeles",
        "station_code": "KPDX",
        "elevation_ft": 50,
        "is_featured": False,
        "description": "秋季降雨頻繁，河谷地區晨霧常見，山區天氣變化快速。",
        "temp": 55,
        "feels": 53,
        "condition": "showers",
        "high": 58,
        "low": 48,
        "humidity": 81,
        "wind_dir": "SW",
        "wind": 7,
        "gust": 15,
        "visibility": "8.0",
        "pressure": "29.90",
        "dew": 50,
        "uv": 2,
        "aqi": 22,
        "summary": "多雲時有陣雨，午後雨勢稍緩；山區道路濕滑。",
        "week": ["showers", "rain", "cloudy", "partly_cloudy", "showers", "cloudy", "partly_cloudy"],
    },
    {
        "name": "Phoenix",
        "state": "AZ",
        "slug": "phoenix-az",
        "county": "Maricopa County",
        "zip_code": "85004",
        "region": "southwest",
        "latitude": 33.4484,
        "longitude": -112.0740,
        "timezone": "America/Phoenix",
        "station_code": "KPHX",
        "elevation_ft": 1086,
        "is_featured": False,
        "description": "沙漠氣候，秋季白天仍炎熱、夜晚涼爽，紫外線強。",
        "temp": 90,
        "feels": 88,
        "condition": "sunny",
        "high": 96,
        "low": 68,
        "humidity": 21,
        "wind_dir": "E",
        "wind": 5,
        "gust": 11,
        "visibility": "10.0",
        "pressure": "29.88",
        "dew": 38,
        "uv": 6,
        "aqi": 52,
        "summary": "晴朗炎熱，午後紫外線很強；入夜後降溫明顯。",
        "week": ["sunny", "sunny", "mostly_sunny", "sunny", "sunny", "mostly_sunny", "sunny"],
    },
]

ALERTS = [
    {
        "slug": "new-york-ny",
        "title": "Coastal Flood Warning",
        "alert_type": "coastal_flood",
        "severity": "severe",
        "urgency": "immediate",
        "areas": "New York County, Brooklyn, Queens",
        "description": (
            "沿海淹水警報生效中。滿潮前後低窪地區可能出現 1–2 英尺的積水，"
            "布魯克林與皇后區濱海路段可能暫時封閉。請避免前往海邊觀浪，"
            "並留意紐約市緊急事務局的最新通知。"
        ),
        "instruction": (
            "- 遠離海灘、碼頭與低窪地區，不要開車穿越積水路段。\n"
            "- 地下停車場與一樓住戶請提前移動車輛與貴重物品。\n"
            "- 留意 NYC Emergency Management 與 NWS 的後續更新。"
        ),
        "start": -2,
        "end": 7,
    },
    {
        "slug": "chicago-il",
        "title": "Wind Advisory",
        "alert_type": "wind",
        "severity": "moderate",
        "urgency": "expected",
        "areas": "Cook County, Chicago Lakefront",
        "description": (
            "冷鋒通過後陣風可達 45 mph，湖邊與高架路段風勢更強。"
            "可能造成路樹斷枝與部分航班延誤。"
        ),
        "instruction": (
            "- 固定陽台與戶外物品，避免在招牌或路樹下停留。\n"
            "- 騎車與高架路段行駛請降低速度，注意側風。\n"
            "- 留意航班與渡輪是否延誤。"
        ),
        "start": 3,
        "end": 14,
    },
    {
        "slug": "miami-fl",
        "title": "Rip Current Risk",
        "alert_type": "rip_current",
        "severity": "moderate",
        "urgency": "expected",
        "areas": "Miami-Dade County beaches",
        "description": (
            "東風與長浪造成離岸流風險提高，今天全天海灘可能出現強勁離岸流。"
            "離岸流不會把泳客拉入海底，但會快速帶離岸邊。"
        ),
        "instruction": (
            "- 不要在無人看管的時段下水。\n"
            "- 若被帶離岸邊，保持冷靜、平行岸邊游動，不要正面逆流。\n"
            "- 海灘掛紅旗時請勿下水。"
        ),
        "start": 0,
        "end": 30,
    },
    {
        "slug": "austin-tx",
        "title": "Severe Thunderstorm Warning",
        "alert_type": "thunderstorm",
        "severity": "severe",
        "urgency": "immediate",
        "areas": "Travis County, western Austin",
        "description": (
            "強烈雷雨胞正通過 Travis County 西部，可能伴隨 60 mph 陣風與冰雹。"
            "請立即進入堅固建築物，遠離窗戶。"
        ),
        "instruction": (
            "- 立即進入室內，避免在空曠處或大樹下停留。\n"
            "- 開車遇到冰雹請減速並尋找有遮蔽的停車地點。\n"
            "- 遠離積水與掉落電線。"
        ),
        "start": -1,
        "end": 4,
    },
    {
        "slug": "new-orleans-la",
        "title": "Flood Watch",
        "alert_type": "flood",
        "severity": "moderate",
        "urgency": "expected",
        "areas": "Orleans Parish, low-lying areas",
        "description": (
            "間歇性強降雨可能造成短時積水，低窪地區與排水較慢的街區需特別留意。"
            "預估 1–2 英吋降雨，局部可達 3 英吋。"
        ),
        "instruction": (
            "- 避免開車穿越積水路段。\n"
            "- 清理住家附近排水口，確保水流順暢。\n"
            "- 留意地方政府發布的淹水與交通管制資訊。"
        ),
        "start": 2,
        "end": 20,
    },
    {
        "slug": "los-angeles-ca",
        "title": "Air Quality Alert",
        "alert_type": "air_quality",
        "severity": "moderate",
        "urgency": "expected",
        "areas": "Los Angeles Basin, San Fernando Valley",
        "description": (
            "盆地逆溫造成污染物累積，AQI 可能達到對敏感族群不健康的等級。"
            "午後海風可望稍微改善。"
        ),
        "instruction": (
            "- 敏感族群減少長時間戶外運動。\n"
            "- 外出可配戴口罩，室內關閉窗戶。\n"
            "- 留意 AirNow 與地方環保局即時資訊。"
        ),
        "start": 0,
        "end": 18,
    },
    {
        "slug": "denver-co",
        "title": "Winter Weather Advisory",
        "alert_type": "winter",
        "severity": "moderate",
        "urgency": "future",
        "areas": "Denver metro, Front Range foothills",
        "description": (
            "週末前段可能出現本季第一場降雪，平地預估 2–4 英吋，山麓地帶可達 6 英吋。"
            "路面可能結冰，行車時間會拉長。"
        ),
        "instruction": (
            "- 提前檢查車輛雪胎與雨刷水。\n"
            "- 預留較長通勤時間，避免急煞。\n"
            "- 山區行程請攜帶保暖衣物與備用糧食。"
        ),
        "start": 30,
        "end": 54,
    },
    {
        "slug": "boston-ma",
        "title": "Frost Advisory",
        "alert_type": "winter",
        "severity": "minor",
        "urgency": "expected",
        "areas": "Suffolk County, inland Boston",
        "description": "今晚至明晨氣溫可能降至 33–36°F，空曠地區有結霜機會。",
        "instruction": (
            "- 將戶外盆栽移入室內或覆蓋保護。\n"
            "- 開車前預留除霜時間。\n"
            "- 留意晨間路面濕滑。"
        ),
        "start": 10,
        "end": 19,
    },
]


class Command(BaseCommand):
    help = "Create or refresh the Skyline Weather demo dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Skip seeding when at least one location already exists.",
        )

    def handle(self, *args, **options):
        if options["if_empty"] and Location.objects.exists():
            self.stdout.write(self.style.WARNING("Locations already exist; skipping seed."))
            return

        self.stdout.write("Seeding Skyline Weather demo data...")
        now = timezone.now()

        for index, data in enumerate(LOCATIONS):
            location, _ = Location.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "state": data["state"],
                    "county": data["county"],
                    "zip_code": data["zip_code"],
                    "region": data["region"],
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "timezone": data["timezone"],
                    "station_code": data["station_code"],
                    "elevation_ft": data["elevation_ft"],
                    "description": data["description"],
                    "is_featured": data["is_featured"],
                },
            )

            CurrentConditions.objects.update_or_create(
                location=location,
                defaults={
                    "temp_f": data["temp"],
                    "feels_like_f": data["feels"],
                    "condition": data["condition"],
                    "humidity": data["humidity"],
                    "wind_direction": data["wind_dir"],
                    "wind_mph": data["wind"],
                    "gust_mph": data["gust"],
                    "visibility_mi": data["visibility"],
                    "pressure_in": data["pressure"],
                    "dew_point_f": data["dew"],
                    "uv_index": data["uv"],
                    "aqi": data["aqi"],
                    "high_f": data["high"],
                    "low_f": data["low"],
                    "summary": data["summary"],
                    "observed_at": now,
                },
            )

            tz = ZoneInfo(data["timezone"])
            local_now = timezone.localtime(now, tz)
            today = local_now.date()

            location.daily.all().delete()
            location.hourly.all().delete()

            daily_rows = []
            day_by_date = {}
            high_offsets = [0, 2, 4, 1, -2, -1, 1]
            low_offsets = [0, 1, 3, 0, -3, -1, 0]
            rotate = index % 3
            for day_index in range(7):
                condition = data["week"][day_index]
                high = data["high"] + high_offsets[(day_index + rotate) % 7]
                low = data["low"] + low_offsets[(day_index + rotate) % 7]
                if low >= high:
                    low = high - 5
                precip = PRECIP.get(condition, 10) + (day_index * 3 + index) % 11
                precip = max(0, min(100, precip))
                wind_low = max(2, data["wind"] - 3 + (day_index % 3))
                wind_high = data["wind"] + 3 + (day_index % 4)
                day = DailyForecast(
                    location=location,
                    date=today + timedelta(days=day_index),
                    condition=condition,
                    high_f=high,
                    low_f=low,
                    precip_percent=precip,
                    wind=f"{data['wind_dir']} {wind_low}–{wind_high} mph",
                    summary=f"{CONDITION_TEXT[condition]} 高溫 {high}°F、低溫 {low}°F。",
                    sunrise=time(7, 10 + (index % 10)),
                    sunset=time(18, 0),
                )
                daily_rows.append(day)
                day_by_date[day.date] = day
            DailyForecast.objects.bulk_create(daily_rows)

            hourly_rows = []
            start_hour = local_now.replace(minute=0, second=0, microsecond=0)
            for hour_index in range(30):
                moment = start_hour + timedelta(hours=hour_index)
                day = day_by_date.get(moment.date())
                if day is None:
                    continue
                base = (day.high_f + day.low_f) / 2
                amplitude = (day.high_f - day.low_f) / 2
                temp = round(base + amplitude * math.sin((moment.hour - 9) / 24 * 2 * math.pi))
                condition = day.condition
                if moment.hour < 6 or moment.hour >= 20:
                    condition = NIGHT_CONDITION.get(condition, condition)
                precip = PRECIP.get(day.condition, 10)
                if precip >= 50:
                    precip = max(15, precip - 20 + (hour_index % 4) * 6)
                else:
                    precip = max(0, precip - 5 + (hour_index % 3) * 5)
                precip = min(100, precip)
                wind = max(0, data["wind"] + (hour_index % 5) - 2)
                hourly_rows.append(
                    HourlyForecast(
                        location=location,
                        time=moment,
                        temp_f=temp,
                        condition=condition,
                        precip_percent=precip,
                        wind_mph=wind,
                        summary=CONDITION_TEXT.get(condition, ""),
                    )
                )
            HourlyForecast.objects.bulk_create(hourly_rows)

        Alert.objects.all().delete()
        for item in ALERTS:
            location = Location.objects.get(slug=item["slug"])
            Alert.objects.create(
                location=location,
                title=item["title"],
                alert_type=item["alert_type"],
                severity=item["severity"],
                urgency=item["urgency"],
                areas=item["areas"],
                description=item["description"],
                instruction=item["instruction"],
                starts_at=now + timedelta(hours=item["start"]),
                ends_at=now + timedelta(hours=item["end"]),
                issued_at=now - timedelta(hours=3),
                source="NWS",
                is_active=True,
            )

        # Demo member account
        demo, created = User.objects.get_or_create(
            username="demo", defaults={"email": "demo@skyline.local"}
        )
        demo.email = "demo@skyline.local"
        demo.first_name = "Ivy"
        demo.last_name = "Lin"
        demo.set_password("Demo1234!")
        demo.save()

        demo_profile, _ = Profile.objects.get_or_create(user=demo)
        demo_profile.display_name = "Ivy Lin"
        demo_profile.unit = "f"
        demo_profile.home_location = Location.objects.get(slug="new-york-ny")
        demo_profile.notify_app = True
        demo_profile.notify_email = True
        demo_profile.notify_sms = False
        demo_profile.min_severity = "moderate"
        demo_profile.save()

        demo.favorites.all().delete()
        for slug in ("new-york-ny", "san-francisco-ca", "seattle-wa"):
            Favorite.objects.create(
                user=demo, location=Location.objects.get(slug=slug)
            )

        demo.search_history.all().delete()
        for query, region, count in [
            ("New York", "northeast", 2),
            ("Seattle", "west", 1),
            ("Chicago", "midwest", 1),
            ("Miami", "southeast", 1),
        ]:
            SearchHistory.objects.create(
                user=demo, query=query, region=region, results_count=count
            )

        # Admin account for the instructor
        admin, _ = User.objects.get_or_create(
            username="admin", defaults={"email": "admin@skyline.local"}
        )
        admin.email = "admin@skyline.local"
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("Admin1234!")
        admin.save()

        admin_profile, _ = Profile.objects.get_or_create(user=admin)
        admin_profile.display_name = "專題管理員"
        admin_profile.home_location = Location.objects.get(slug="new-york-ny")
        admin_profile.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Location.objects.count()} locations, "
                f"{DailyForecast.objects.count()} daily forecasts, "
                f"{HourlyForecast.objects.count()} hourly forecasts, "
                f"{Alert.objects.count()} alerts."
            )
        )
        self.stdout.write("Demo member: demo / Demo1234!   Admin: admin / Admin1234!")
