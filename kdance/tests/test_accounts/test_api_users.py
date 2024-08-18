"""Tests related to Users API view."""
import pytest

from copy import deepcopy

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from parameterized import parameterized

from accounts.api.views import UsersApiViewSet
from members.models import Payment, Season
from tests.authentication import AuthenticatedAction, AuthTestCase
from tests.data_tests import TESTUSER, TESTUSER_EMAIL


@pytest.mark.django_db
class TestUsersView(AuthTestCase):
    view_url = reverse('api-users-list')
    view_function = UsersApiViewSet

    _TEST_DATA = {
        "username": "pliploup",
        "first_name": "Plip",
        "last_name": "Plop",
        "email": "plip@plop.fr",
        "address": "This way",
        "phone": "0666666666",
        "password": "SuperM0tdePass3",
    }

    @parameterized.expand([
        ("get", 403, 200, None),
        ("get", 403, 405, reverse("api-users-detail", args=[1])),
        ("post", 400, 400, None),
        ("put", 403, 405, reverse("api-users-detail", args=[1])),
        ("patch", 403, 405, reverse("api-users-detail", args=[1])),
    ])
    def test_permissions(self, method, user_status, superuser_status, url):
        url = url or self.view_url
        assert self.users_have_permission(
            urls=(url, self.view_function),
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    def test_delete_permissions(self):
        def gen_pk():
            val = 0
            new_user = User.objects.create(username=f"user{val}", email=f"email{val}@test.fr")
            yield new_user.pk
            val += 1

        assert self.users_have_permission(
            urls=(reverse("api-users-detail", args=[next(gen_pk())]), self.view_function),
            method="delete",
            user_status=403,
            superuser_status=204,
        )

    @parameterized.expand([
        ("get", None),
        ("get", reverse("api-users-detail", args=[1])),
        ("post", None),
        ("put", reverse("api-users-detail", args=[1])),
        ("patch", reverse("api-users-detail", args=[1])),
        ("delete", reverse("api-users-detail", args=[1])),
    ])
    def test_authentication_mandatory(self, method, url):
        """Mandatory except for POST (user creation)."""
        url = url or self.view_url
        status = 400 if method == "post" else 403
        assert self.anonymous_has_permission(
            method=method,
            status=status,
            urls=[url],
        )

    def test_get(self):
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 200, response
            response_json = response.json()
            assert len(response_json) == 3  # kdance, testuser, super_testuser
            super_user = next(user for user in response_json if user["username"] == self.super_testuser.username)
            assert super_user["email"] == self.super_testuser.email
            assert super_user["profile"]["address"] == self.super_testuser.profile.address

    def test_post_authenticated(self):
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(self.view_url, data=self._TEST_DATA, content_type="application/json")
            assert response.status_code == 201, response
            new_user = User.objects.last()
            assert new_user.first_name == self._TEST_DATA["first_name"]
            assert new_user.profile.phone == self._TEST_DATA["phone"]
            assert new_user.check_password(self._TEST_DATA["password"])
            assert "password" not in response.json()
            assert len(mail.outbox) == 1
            email_sent = mail.outbox[0]
            assert email_sent.subject == "Création d'un compte K'Dance"
            assert list(email_sent.to) == [self._TEST_DATA["email"]]

    @parameterized.expand([True, False])
    def test_post_not_authenticated(self, with_season):
        if with_season:
            season = Season.objects.create(year="2010-2011", is_current=True)
        response = self.client.post(self.view_url, data=self._TEST_DATA, content_type="application/json")
        assert response.status_code == 201, response
        new_user = User.objects.last()
        assert new_user.first_name == self._TEST_DATA["first_name"]
        assert new_user.profile.phone == self._TEST_DATA["phone"]
        assert new_user.check_password(self._TEST_DATA["password"])
        assert "password" not in response.json()
        email_sent = mail.outbox[0]
        assert email_sent.subject == "Création d'un compte K'Dance"
        assert list(email_sent.to) == [self._TEST_DATA["email"]]
        if with_season:
            assert Payment.objects.filter(user=new_user, season=season).exists()
        else:
            assert Payment.objects.count() == 0

    @parameterized.expand([
        ("", "username", "Ce champ ne peut être vide."),
        (TESTUSER, "username", "Cet identifiant est déjà pris."),
        ("TestUser", "username", "Cet identifiant est déjà pris."),
        ("", "email", "Ce champ ne peut être vide."),
        (TESTUSER_EMAIL, "email", "Un utilisateur est déjà associé à cet email."),
        ("TEST@Kdance.com", "email", "Un utilisateur est déjà associé à cet email."),
        ("plop.com", "email", "Cette adresse email ne semble pas avoir un format valide."),
        ("", "phone", "Ce champ ne peut être vide."),
        ("+336", "phone", "Ce numéro de téléphone n'est pas valide. Format attendu: 0123456789."),
        ("", "address", "Ce champ ne peut être vide."),
        ("", "first_name", "Ce champ ne peut être vide."),
        ("", "last_name", "Ce champ ne peut être vide."),
    ])
    def test_post_payload_error(self, value, key, message):
        data = deepcopy(self._TEST_DATA)
        data[key] = value
        response = self.client.post(self.view_url, data=data, content_type="application/json")
        assert response.status_code == 400, response
        assert message in response.json()[key]

    def test_post_payload_format(self):
        """Test that names and emails are correctly formatted."""
        response = self.client.post(
            self.view_url,
            data={
                "username": "Pliploup",
                "first_name": "plIp pliP",
                "last_name": "plop",
                "email": "pLip@plop.FR",
                "address": "This way",
                "phone": "0666666666",
                "password": "SuperM0tdePass3",
            },
            content_type="application/json",
        )
        assert response.status_code == 201, response
        response_json = response.json()
        assert response_json["first_name"] == "Plip Plip"
        assert response_json["last_name"] == "Plop"
        assert response_json["email"] == "plip@plop.fr"
        assert response_json["username"] == "Pliploup"

    def test_delete_kdance_impossible(self):
        """Tests that automatic superuser kdance cannot be deleted."""
        superuser = User.objects.get(username=settings.SUPERUSER_EMAIL)
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.delete(reverse("api-users-detail", args=[superuser.pk]))
            assert response.status_code == 401


@pytest.mark.django_db
class TestUsersAdminView(AuthTestCase):
    view_function = UsersApiViewSet
    _kwargs = {}

    _tmp_user: User | None = None

    @pytest.fixture(autouse=True)
    def set_tmp_user(self):
        tmp_user, _ = User.objects.get_or_create(username="tmpuser", email="tmp@mail.fr")
        self._tmp_user = tmp_user

    @property
    def view_url(self):
        return reverse('api-users-admin', kwargs=self._kwargs)

    @parameterized.expand([
        ("get", 403, 405),
        ("post", 405, 405),  # simple user allowed to create user (but POST not allowed on this url)
        ("put", 403, 400),
        ("patch", 403, 405),
        ("delete", 403, 405),
    ])
    def test_permissions(self, method, user_status, superuser_status):
        self._kwargs["action"] = "activate"
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )
        self._kwargs["action"] = "deactivate"
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    @parameterized.expand([
        "get", "post", "put", "patch", "delete",
    ])
    def test_authentication_mandatory(self, method):
        # POST does not require authentication for user creation, but does not exist on this url, thus 405.
        status = 405 if method == "post" else 403
        assert self.anonymous_has_permission(method, status)

    @parameterized.expand([
        (None, "activate", 200, None, [], []),
        ([], "activate", 400, [], [], []),
        ([TESTUSER_EMAIL], "activate", 200, [TESTUSER_EMAIL], [], []),
        (["Test@KDance.COM"], "activate", 200, [TESTUSER_EMAIL], [], []),
        ([TESTUSER_EMAIL, "plip@plop.fr"], "activate", 200, [TESTUSER_EMAIL], ["plip@plop.fr"], []),
        (["plip@plop.fr"], "activate", 400, [], ["plip@plop.fr"], []),
        (None, "deactivate", 200, None, [], []),
        ([], "deactivate", 400, [], [], []),
        ([TESTUSER_EMAIL], "deactivate", 200, [TESTUSER_EMAIL], [], []),
        (["Test@KDance.COM"], "deactivate", 200, [TESTUSER_EMAIL], [], []),
        ([TESTUSER_EMAIL, "plip@plop.fr"], "deactivate", 200, [TESTUSER_EMAIL], ["plip@plop.fr"], []),
        (["plip@plop.fr"], "deactivate", 400, [], ["plip@plop.fr"], []),
    ])
    def test_put(self, emails, action, status_code, processed, not_found, other):
        emails = [TESTUSER_EMAIL, self._tmp_user.email] if emails is None else emails
        processed = [TESTUSER_EMAIL, self._tmp_user.email] if processed is None else processed
        self._kwargs["action"] = action
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.put(
                self.view_url,
                data={"emails": emails},
                content_type="application/json",
            )
            assert response.status_code == status_code, response
            response_json = response.json()
            assert response_json["processed"] == processed
            assert response_json["not_found"] == not_found
            assert response_json["other"] == other
        for email in processed:
            assert User.objects.get(email=email).is_superuser is (action == "activate")

    def test_put_action_error(self):
        self._kwargs["action"] = "action"
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.put(
                self.view_url,
                data={"emails": []},
                content_type="application/json",
            )
            assert response.status_code == 404, response

    def test_put_deactivate_kdance_impossible(self):
        self._kwargs["action"] = "deactivate"
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.put(
                self.view_url,
                data={"emails": [settings.SUPERUSER_EMAIL, self._tmp_user.email]},
                content_type="application/json",
            )
            assert response.status_code == 400, response
            assert f"{settings.SUPERUSER_EMAIL}: cet utilisateur ne peut pas être supprimé des administrateurs." in response.json()["emails"]
            assert User.objects.get(username=settings.SUPERUSER_EMAIL).is_superuser is True