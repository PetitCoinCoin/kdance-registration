"""Tests related to Payment and Check API views."""
from urllib.parse import urlencode

import pytest

from django.conf import settings
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from parameterized import parameterized

from members.api.views import CheckViewSet, PaymentViewSet
from members.models import Check, Payment, Season
from tests.authentication import AuthenticatedAction, AuthTestCase


@pytest.mark.django_db
class TestCheckApiView(AuthTestCase):
    view_url = reverse("api-checks-list")
    view_function = CheckViewSet

    def setup_list(self) -> tuple[Season]:
        season_1 = Season.objects.create(year="1900-1901", is_current=False)
        season_2 = Season.objects.create(year="2000-2001", is_current=True)
        for i, season in enumerate([season_1, season_2]):
            payment = self.testuser.payment_set.filter(season=season).first()
            for val in range(1, 4):
                Check.objects.create(
                    number=(i + 1) * 1000 + val,
                    name=self.testuser.username,
                    bank="bankbank",
                    amount=(i + 1) * 10 + val,
                    month=val,
                    payment=payment,
                )
        assert Check.objects.count() == 6
        return season_1, season_2

    @parameterized.expand([
        ("get", 403, 200),
        ("post", 403, 405),
    ])
    def test_permissions(self, method, user_status, superuser_status):
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    def test_no_detail_view(self):
        with pytest.raises(NoReverseMatch):
            reverse("api-checks-details", kwargs={"pk": 1})

    def test_authentication_mandatory(self):
        assert self.anonymous_has_permission("get", 403)

    def test_get_list(self):
        self.setup_list()
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 200, response
            response_json = response.json()
            assert len(response_json) == 6
            # test sorting: decreasing season year, then month (then bank - but not tested)
            assert response_json[0]["number"] == 2001  # season 2, month 1
            assert response_json[0]["amount"] == 21
            assert response_json[0]["month"] == 1
            assert response_json[-1]["number"] == 1003  # season 1, month 3
            assert response_json[-1]["amount"] == 13
            assert response_json[-1]["month"] == 3

    @parameterized.expand([
        ({"season": 1}, 3),
        ({"month": 1}, 2),
        ({"season": 1, "month": 1}, 1),
        ({"plop": "plup"}, 6),
    ])
    def test_get_filter(self, query_params, count):
        season_1, season_2 = self.setup_list()
        if query_params.get("season"):
            query_params["season"] = season_1.pk if 1 else season_2.pk
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(f"{self.view_url}?{urlencode(query_params)}")
            assert response.status_code == 200, response
            response_json = response.json()
            assert len(response_json) == count


@pytest.mark.django_db
class TestPaymentApiView(AuthTestCase):
    view_function = PaymentViewSet
    _kwargs = {}

    _season: Season| None = None

    @pytest.fixture(autouse=True)
    def set_season(self):
        # It automatically created Payment for existing users
        season, _ = Season.objects.get_or_create(year="1900-1901", is_current=False)
        self._season = season

    @property
    def view_url(self):
        return reverse(
            f"api-payments-{'detail' if 'pk' in self._kwargs else 'list'}",
            kwargs=self._kwargs,
        )

    @parameterized.expand([
        ("get", 403, 200, False),
        ("get", 403, 405, True),
        ("post", 403, 405, False),
        ("put", 403, 405, True),
        ("patch", 403, 200, True),
        ("delete", 403, 405, True),
    ])
    def test_permissions(self, method, user_status, superuser_status, with_pk):
        self._kwargs = {"pk": self.testuser.payment_set.first().pk} if with_pk else {}
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
        self._kwargs = {"pk": self.testuser.payment_set.first().pk} if with_pk else {}
        assert self.anonymous_has_permission(method, 403)

    def test_get_list(self):
        self._kwargs = {}
        # setup
        self.testuser.last_name = "Testuser"
        self.testuser.save()
        self.super_testuser.last_name = "Superuser"
        self.super_testuser.save()
        new_season = Season.objects.create(year="2000-2001", is_current=True)
        for p in Payment.objects.all():
            p.comment = p.user.username
            p.save()

        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 200, response
            response_json = response.json()
            assert len(response_json) == 6  # Don't forget permanent superuser !
            # test sorting: decreasing season year, then user last name (then first name - but not tested)
            assert response_json[0]["season"]["id"] == new_season.pk
            assert response_json[0]["comment"] == settings.SUPERUSER_EMAIL
            assert response_json[-1]["season"]["id"] == self._season.pk
            assert response_json[-1]["comment"] == self.testuser.username

    @parameterized.expand([
        ("ancv", {"amount": 10, "count": 2}, 10, 0),
        ("other_payment", {"amount": 100, "comment": "crypto"}, 100, 0),
        ("comment", "C'est cadeau", 0, 0),
        ("refund", 50, 0, 0),
        ("special_discount", 50, 0, -50),
        ("check_payment", [{"amount": 10.0, "bank": "bank", "month": 1, "name": "Bob", "number": 10}], 10, 0),
    ])
    def test_patch(self, key, value, paid, due):
        self._kwargs = {"pk": self.testuser.payment_set.first().pk}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(
                self.view_url,
                data={key: value},
                content_type="application/json",
            )
            assert response.status_code == 200, response
            response_json = response.json()
            if key == "check_payment":
                for k, v in value[0].items():
                    assert response_json[key][0][k] == v
            else:
                assert response_json[key] == value
        self.testuser.refresh_from_db()
        assert self.testuser.payment_set.first().paid == paid
        assert self.testuser.payment_set.first().due == due

    @parameterized.expand([
        ("ancv", {"amount": 0, "count": 2}, "amount", "Une valeur non nulle est obligatoire."),
        ("ancv", {"amount": 10, "count": 0}, "count", "Une valeur non nulle est obligatoire."),
        ("other_payment", {"amount": 100, "comment": ""}, "comment", "Ce champ ne peut être vide."),
        ("sport_coupon", {"amount": 10, "count": 0}, "count", "Une valeur non nulle est obligatoire."),
        ("check_payment", [{"amount": 10, "bank": "bank", "month": 1, "name": "", "number": 10}], "name", "Ce champ ne peut être vide."),
    ])
    def test_patch_payload_error(self, key, value, subkey, message):
        self._kwargs = {"pk": self.testuser.payment_set.first().pk}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(
                self.view_url,
                data={key: value},
                content_type="application/json",
            )
            assert response.status_code == 400, response
            if isinstance(value, list):
                assert message in response.json()[key][0][subkey]
            else:
                assert message in response.json()[key][subkey]
