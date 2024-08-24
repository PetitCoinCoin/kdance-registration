"""Tests related to Course API view."""
from datetime import datetime, time, timezone

import pytest

from django.urls import reverse
from parameterized import parameterized

from members.api.views import CourseViewSet
from members.models import (
    Course,
    Documents,
    Member,
    Season,
)
from tests.authentication import AuthenticatedAction, AuthTestCase


@pytest.mark.django_db
class TestCourseApiView(AuthTestCase):
    view_function = CourseViewSet
    _kwargs = {}

    _course: Course | None = None
    _season: Season | None = None

    @pytest.fixture(autouse=True)
    def set_course(self):
        self._season, _ = Season.objects.get_or_create(year="1900-1901")
        self._course, _ = Course.objects.get_or_create(
            name="Cha cha cha",
            season=self._season,
            price=10,
            weekday=0,
            start_hour=time(10, 0),
            end_hour=time(11, 0),
        )

    @property
    def view_url(self):
        return reverse(
            f"api-courses-{'detail' if 'pk' in self._kwargs else 'list'}",
            kwargs=self._kwargs,
        )

    @parameterized.expand([
        ("get", 200, 200, False),
        ("get", 200, 200, True),
        ("post", 403, 400, False),
        ("put", 403, 405, True),
        ("patch", 403, 200, True),
        ("delete", 403, 204, True),
    ])
    def test_permissions(self, method, user_status, superuser_status, with_pk):
        self._kwargs = {"pk": self._course.pk} if with_pk else {}
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    @parameterized.expand([
        ("get", False),
        ("get", True),
        ("post", False),
        ("put", True),
        ("patch", True),
        ("delete", True),
    ])
    def test_authentication_mandatory(self, method, with_pk):
        self._kwargs = {"pk": self._course.pk} if with_pk else {}
        assert self.anonymous_has_permission(method, 403)

    def test_post(self):
        data = {
            "name": "Chenille",
            "season": self._season.pk,
            "price": 100,
            "weekday": 6,
            "start_hour": time(18, 0),
            "end_hour": time(20, 0),
        }
        self._kwargs = {}
        assert Course.objects.count() == 1
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 201, response
            response_json = response.json()
            assert response_json["name"] == "Chenille"
        assert Course.objects.count() == 2

    @parameterized.expand([
        (10, True, "n'est pas un choix valide.", "weekday"),  # invalid weekday
        (6, False, "l'objet n'existe pas.", "season"),  # invalid season
        (0, True, "doivent former un ensemble unique.", "non_field_errors"),  # duplicate course
    ])
    def test_post_payload_error(self, weekday, season, message, key):
        data = {
            "name": "Cha cha cha",
            "season": self._season.pk if season else 0,
            "price": 100,
            "weekday": weekday,
            "start_hour": time(10, 0),
            "end_hour": time(11, 0),
        }
        self._kwargs = {}
        assert Course.objects.count() == 1
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 400, response
            response_json = response.json()
            assert message in response_json[key][0]
        assert Course.objects.count() == 1

    @parameterized.expand([
        ("Chenille", None, None, None),
        (None, 6, None, None),
        (None, None, 20, None),
        (None, None, None, 1000),
    ])
    def test_patch(self, name, weekday, start, price):
        data = {}
        if name:
            data["name"] = name
        if weekday:
            data["weekday"] = weekday
        if start:
            data["start_hour"] = time(start, 0)
        if price:
            data["price"] = price
        self._kwargs["pk"] = self._course.pk
        assert Course.objects.count() == 1

        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 200, response
        assert Course.objects.count() == 1
        self._course.refresh_from_db()
        if name:
            assert self._course.name == name
        if weekday:
            assert self._course.weekday == weekday
        if start:
            assert self._course.start_hour == time(start, 0)
        if price:
            assert self._course.price == price

    def test_patch_payload_error(self):
        data = {"weekday": 10}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 400, response
            assert "n'est pas un choix valide." in response.json()["weekday"][0]

    def test_delete(self):
        self._kwargs["pk"] = self._course.pk
        assert Course.objects.count() == 1
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.delete(self.view_url)
            assert response.status_code == 204, response
        assert Course.objects.count() == 0


@pytest.mark.django_db
class TestCoursesCopyApiView(AuthTestCase):
    view_function = CourseViewSet
    view_url = reverse("api-courses-copy-season")

    _course: Course | None = None
    _season: Season | None = None

    @pytest.fixture(autouse=True)
    def set_course(self):
        self._season, _ = Season.objects.get_or_create(year="1900-1901")
        self._course, _ = Course.objects.get_or_create(
            name="Cha cha cha",
            season=self._season,
            price=10,
            weekday=0,
            start_hour=time(10, 0),
            end_hour=time(11, 0),
        )

    @parameterized.expand([
        ("get", 405, 405),
        ("post", 403, 400),
        ("put", 403, 405),
        ("patch", 403, 405),
        ("delete", 403, 405),
    ])
    def test_permissions(self, method, user_status, superuser_status):
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    def test_authentication_mandatory(self):
        assert self.anonymous_has_permission("put", 403)

    def test_copy_season(self):
        new_season = Season.objects.create(year="2000-2001")
        data = {
            "from_season": self._season.pk,
            "to_season": new_season.pk,
        }
        assert Course.objects.count() == 1
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 200, response
        assert Course.objects.count() == 2
        new_course = Course.objects.last()
        for attr in (
            "name",
            "weekday",
            "price",
            "start_hour",
            "end_hour",
        ):
            assert getattr(new_course, attr) == getattr(self._course, attr)
        assert new_course.season == new_season

    @parameterized.expand([True, False])
    def test_copy_season_error(self, is_from_ok):
        data = {
            "from_season": self._season.pk if is_from_ok else 0,
            "to_season": 0 if is_from_ok else self._season.pk,
        }
        assert Course.objects.count() == 1
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 400, response
            assert "Cette saison n'existe pas." in response.json()["to_season" if is_from_ok else "from_season"][0]
        assert Course.objects.count() == 1
