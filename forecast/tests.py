from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Alert,
    CurrentConditions,
    DailyForecast,
    Favorite,
    HourlyForecast,
    Location,
    Profile,
    SearchHistory,
)


class SkylineTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location = Location.objects.create(
            name="New York",
            state="NY",
            slug="new-york-ny",
            county="New York County",
            zip_code="10001",
            region="northeast",
            latitude=Decimal("40.712800"),
            longitude=Decimal("-74.006000"),
            timezone="America/New_York",
            station_code="KNYC",
            elevation_ft=33,
            is_featured=True,
            description="Test city",
        )
        cls.other = Location.objects.create(
            name="Seattle",
            state="WA",
            slug="seattle-wa",
            county="King County",
            zip_code="98101",
            region="west",
            latitude=Decimal("47.606200"),
            longitude=Decimal("-122.332100"),
            timezone="America/Los_Angeles",
            station_code="KSEA",
            elevation_ft=187,
            is_featured=True,
        )
        CurrentConditions.objects.create(
            location=cls.location,
            temp_f=58,
            feels_like_f=56,
            condition="partly_cloudy",
            humidity=58,
            wind_direction="NW",
            wind_mph=8,
            gust_mph=16,
            visibility_mi=Decimal("10.0"),
            pressure_in=Decimal("30.12"),
            dew_point_f=43,
            uv_index=3,
            aqi=32,
            high_f=61,
            low_f=48,
            summary="Clouds and sun.",
        )
        CurrentConditions.objects.create(
            location=cls.other,
            temp_f=54,
            feels_like_f=51,
            condition="rain",
            humidity=86,
            wind_direction="S",
            wind_mph=9,
            high_f=57,
            low_f=47,
            summary="Rain.",
        )
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        for index in range(7):
            DailyForecast.objects.create(
                location=cls.location,
                date=timezone.localdate() + timedelta(days=index),
                condition="partly_cloudy",
                high_f=61 + index,
                low_f=48 + index,
                precip_percent=10 * index,
                wind="NW 5–10 mph",
                summary="Test day",
            )
        for index in range(24):
            HourlyForecast.objects.create(
                location=cls.location,
                time=now + timedelta(hours=index),
                temp_f=58 + index % 5,
                condition="partly_cloudy",
                precip_percent=5,
                wind_mph=8,
            )
        cls.alert = Alert.objects.create(
            location=cls.location,
            title="Coastal Flood Warning",
            alert_type="coastal_flood",
            severity="severe",
            urgency="immediate",
            areas="New York County",
            description="Coastal flooding expected.",
            instruction="- Avoid low lying areas.\n- Move vehicles.",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(hours=6),
            issued_at=now - timedelta(hours=2),
            source="NWS",
        )
        cls.demo = User.objects.create_user(
            username="demo", password="Demo1234!", email="demo@skyline.local"
        )
        profile, _ = Profile.objects.get_or_create(user=cls.demo)
        profile.home_location = cls.location
        profile.save()
        Favorite.objects.create(user=cls.demo, location=cls.location)
        SearchHistory.objects.create(
            user=cls.demo, query="New York", results_count=1
        )
        cls.admin = User.objects.create_superuser(
            username="admin", password="Admin1234!", email="admin@skyline.local"
        )

    def test_public_pages_render(self):
        for name in ["home", "locations", "alerts"]:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
        response = self.client.get(self.location.get_absolute_url())
        self.assertContains(response, "New York, NY")
        response = self.client.get(self.alert.get_absolute_url())
        self.assertContains(response, "Coastal Flood Warning")

    def test_search_and_filters(self):
        response = self.client.get(
            reverse("locations"),
            {"q": "Seattle", "region": "west", "condition": "rain", "temp_min": 50},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seattle")
        self.assertNotContains(response, 'href="/locations/new-york-ny/"')

    def test_alert_filters(self):
        response = self.client.get(reverse("alerts"), {"severity": "severe"})
        self.assertContains(response, "Coastal Flood Warning")
        response = self.client.get(reverse("alerts"), {"severity": "minor"})
        self.assertNotContains(response, "Coastal Flood Warning")

    def test_search_suggestions_api(self):
        response = self.client.get(reverse("search_suggestions"), {"q": "New"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["results"][0]["label"], "New York, NY")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_member_dashboard_and_profile(self):
        self.client.login(username="demo", password="Demo1234!")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New York, NY")
        response = self.client.post(
            reverse("dashboard"),
            {
                "display_name": "Demo User",
                "unit": "c",
                "home_location": self.other.pk,
                "min_severity": "severe",
                "notify_app": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        profile = Profile.objects.get(user=self.demo)
        self.assertEqual(profile.display_name, "Demo User")
        self.assertEqual(profile.unit, "c")
        self.assertEqual(profile.home_location, self.other)

    def test_favorite_toggle(self):
        self.client.login(username="demo", password="Demo1234!")
        response = self.client.post(
            reverse("toggle_favorite", args=[self.other.slug]), {"next": reverse("dashboard")}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Favorite.objects.filter(user=self.demo, location=self.other).exists()
        )
        self.client.post(
            reverse("toggle_favorite", args=[self.other.slug]), {"next": reverse("dashboard")}
        )
        self.assertFalse(
            Favorite.objects.filter(user=self.demo, location=self.other).exists()
        )

    def test_unit_toggle_changes_display(self):
        response = self.client.get(reverse("set_unit", args=["c"]), {"next": reverse("home")})
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "14°")

    def test_registration_creates_profile(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newmember",
                "email": "new@example.com",
                "display_name": "New Member",
                "password1": "Skyline!2345",
                "password2": "Skyline!2345",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newmember")
        self.assertTrue(Profile.objects.filter(user=user, display_name="New Member").exists())

    def test_staff_can_reach_admin(self):
        self.client.login(username="admin", password="Admin1234!")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/admin/forecast/alert/")
        self.assertContains(response, "Coastal Flood Warning")

    def test_healthcheck(self):
        response = self.client.get(reverse("healthz"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_filter_page_has_pagination_and_is_active(self):
        response = self.client.get(reverse("locations"))
        self.assertContains(response, "共 <strong>2</strong> 個符合條件的城市", html=False)
