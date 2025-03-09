"""Tests related to Season API view."""

from urllib.parse import urlencode

import pytest

from django.urls import reverse
from parameterized import parameterized

from members.api.views import SeasonViewSet
from members.models import Season
from tests.authentication import AuthenticatedAction, AuthTestCase


@pytest.mark.django_db
class TestSeasonApiView(AuthTestCase):
    view_function = SeasonViewSet
    _kwargs = {}

    _season: Season | None = None

    @pytest.fixture(autouse=True)
    def set_season(self):
        season, _ = Season.objects.get_or_create(year="1900-1901", is_current=True)
        self._season = season

    @property
    def view_url(self):
        return reverse(
            f"api-seasons-{'detail' if 'pk' in self._kwargs else 'list'}",
            kwargs=self._kwargs,
        )

    @parameterized.expand(
        [
            ("get", 200, 200, False),
            ("get", 200, 200, True),
            ("post", 403, 400, False),
            ("put", 403, 405, True),
            ("patch", 403, 200, True),
            ("delete", 403, 204, True),
        ]
    )
    def test_permissions(self, method, user_status, superuser_status, with_pk):
        self._kwargs = {"pk": self._season.pk} if with_pk else {}
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    @parameterized.expand(
        [
            ("get", False),
            ("get", True),
            ("post", False),
            ("put", True),
            ("patch", True),
            ("delete", True),
        ]
    )
    def test_authentication_mandatory(self, method, with_pk):
        self._kwargs = {"pk": self._season.pk} if with_pk else {}
        assert self.anonymous_has_permission(method, 403)

    def test_get_list(self):
        self._kwargs = {}
        assert Season.objects.count() == 1
        last_season = Season.objects.create(year="2000-2001")
        mid_season = Season.objects.create(year="1950-1951")
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 200, response
            response_json = response.json()
            assert len(response_json) == 3
            # test sorting, last season (in term of year) first
            assert response_json[0]["id"] == last_season.pk
            assert response_json[1]["id"] == mid_season.pk

    @parameterized.expand(
        [
            ("is_current", True, 1),
            ("is_current", "True", 1),
            ("is_current", 1, 1),
            ("is_current", False, 2),
            ("is_current", "False", 2),
            ("is_current", 0, 2),
            ("is_current", "plop", 3),
            ("plop", "plip", 3),
        ]
    )
    def test_get_list_filter(self, key, value, count):
        self._kwargs = {}
        season_1 = Season.objects.create(year="2000-2001", is_current=False)
        season_2 = Season.objects.create(year="1950-1951", is_current=False)
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(f"{self.view_url}?{urlencode({key: value})}")
            assert response.status_code == 200, response
            response_json = response.json()
            assert len(response_json) == count
            if count == 1:
                assert response_json[0]["id"] == self._season.pk
            elif count == 2:
                assert [s["id"] for s in response_json] == [season_1.pk, season_2.pk]

    def test_get_one(self):
        new_season = Season.objects.create(year="2000-2001")
        self._kwargs = {"pk": new_season.pk}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 200, response
            response_json = response.json()
            assert response_json["id"] == new_season.pk
            assert response_json["year"] == new_season.year

    @parameterized.expand([False, True, None])
    def test_post(self, is_current):
        year = "2000-2001"
        data = {"year": year}
        if is_current is not None:
            data["is_current"] = is_current
        assert self._season.is_current
        self._kwargs = {}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(
                self.view_url,
                data=data,
                content_type="application/json",
            )
            assert response.status_code == 201, response
            assert response.json()["year"] == year
            assert response.json()["pass_sport_amount"] == 50  # default
            assert (
                response.json()["is_current"] is is_current
                if is_current is not None
                else True
            )
        if is_current is None or is_current:
            self._season.refresh_from_db()
            assert not self._season.is_current

    @parameterized.expand(
        [
            ("2000-01", "Saisissez une valeur valide."),
            ("1800-1801", "On ne peut pas créer de saison dans le passé !"),
        ]
    )
    def test_post_payload_error(self, year, message):
        self._kwargs = {}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(
                self.view_url,
                data={"year": year},
                content_type="application/json",
            )
            assert response.status_code == 400, response
            assert message in response.json()["year"]

    def test_patch(self):
        new_season = Season.objects.create(year="2000-2001", is_current=False)
        new_year = "2010-2011"
        assert self._season.is_current
        self._kwargs = {"pk": new_season.pk}

        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(
                self.view_url,
                data={"year": new_year, "is_current": True},
                content_type="application/json",
            )
            assert response.status_code == 200, response
            assert response.json()["year"] == new_year
            assert response.json()["is_current"] is True
        # new_season is now the only current season
        self._season.refresh_from_db()
        assert not self._season.is_current
        new_season.refresh_from_db()
        assert new_season.is_current

        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(
                self.view_url,
                data={"is_current": False},
                content_type="application/json",
            )
            assert response.status_code == 200, response
            assert response.json()["year"] == new_year
            assert response.json()["is_current"] is False
        # no current season anymore
        self._season.refresh_from_db()
        assert not self._season.is_current
        new_season.refresh_from_db()
        assert not new_season.is_current

    @parameterized.expand(
        [
            ("2000-01", "Saisissez une valeur valide."),
            ("1800-1801", "On ne peut pas créer de saison dans le passé !"),
        ]
    )
    def test_patch_payload_error(self, year, message):
        self._kwargs = {"pk": self._season.pk}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(
                self.view_url,
                data={"year": year},
                content_type="application/json",
            )
            assert response.status_code == 400, response
            assert message in response.json()["year"]

    def test_delete(self):
        self._kwargs = {"pk": self._season.pk}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.delete(self.view_url)
            assert response.status_code == 204, response
        assert Season.objects.count() == 0
