"""Tests related to UserMe API view."""

import pytest

from copy import deepcopy
from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from parameterized import parameterized

from accounts.api.views import UserMeApiViewSet
from members.models import Documents, Member, Season
from tests.authentication import AuthenticatedAction, AuthTestCase
from tests.data_tests import SUPERTESTUSER, SUPERTESTUSER_EMAIL


@pytest.mark.django_db
class TestUserMeView(AuthTestCase):
    view_url = reverse("api-user-me")
    view_function = UserMeApiViewSet

    _TEST_DATA = {
        "first_name": "Plip",
        "last_name": "Plop",
        "email": "plip@plop.fr",
        "profile": {
            "address": "This way",
            "city": "Là",
            "postal_code": "31000",
            "phone": "0666666666",
        },
    }

    @parameterized.expand(
        [
            ("get", 200, 200),
            ("post", 405, 405),
            ("put", 405, 405),
            ("patch", 200, 200),
        ]
    )
    def test_permissions(self, method, user_status, superuser_status):
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    @parameterized.expand(
        [
            "get",
            "post",
            "put",
            "patch",
            "delete",
        ]
    )
    def test_authentication_mandatory(self, method):
        assert self.anonymous_has_permission(method, 403)

    def test_get(self):
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 200, response
            response_json = response.json()
            assert response_json["username"] == self.testuser.username
            assert response_json["email"] == self.testuser.email
            assert response_json["profile"]["address"] == self.testuser.profile.address

    def test_patch(self):
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.patch(
                self.view_url, data=self._TEST_DATA, content_type="application/json"
            )
            assert response.status_code == 200, response
            self.testuser.refresh_from_db()
            assert self.testuser.first_name == self._TEST_DATA["first_name"]
            assert self.testuser.profile.phone == self._TEST_DATA["profile"]["phone"]

    @parameterized.expand(
        [
            ("", None, None, "Ce champ ne peut être vide."),
            (SUPERTESTUSER, None, None, "Cet identifiant est déjà pris."),
            ("SUPER_testuser", None, None, "Cet identifiant est déjà pris."),
            (None, "", None, "Ce champ ne peut être vide."),
            (
                None,
                SUPERTESTUSER_EMAIL,
                None,
                "Un utilisateur est déjà associé à cet email.",
            ),
            (
                None,
                "TESTSUPER@kdance.COM",
                None,
                "Un utilisateur est déjà associé à cet email.",
            ),
            (
                None,
                "plop.com",
                None,
                "Cette adresse email ne semble pas avoir un format valide.",
            ),
            (None, None, "+336", "Saisissez une valeur valide."),
            (None, None, "", "Ce champ ne peut être vide."),
        ]
    )
    def test_patch_payload_error(self, username, email, phone, message):
        data = deepcopy(self._TEST_DATA)
        if username is not None:
            data["username"] = username
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["profile"]["phone"] = phone
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.patch(
                self.view_url, data=data, content_type="application/json"
            )
            assert response.status_code == 400
            if username is not None:
                assert message in response.json()["username"]
            if email is not None:
                assert message in response.json()["email"]
            if phone is not None:
                assert message in response.json()["profile"]["phone"]

    def test_patch_member_cascade_update(self):
        season, _ = Season.objects.get_or_create(
            year="1900-1901",
            ffd_a_amount=0,
            ffd_b_amount=0,
            ffd_c_amount=0,
            ffd_d_amount=0,
        )
        doc, _ = Documents.objects.get_or_create(
            authorise_photos=False,
            authorise_emergency=False,
        )
        member, _ = Member.objects.get_or_create(
            user=self.testuser,
            season=season,
            first_name="Plip",
            last_name="Plop",
            birthday=datetime(1900, 5, 1, tzinfo=timezone.utc),
            address=self.testuser.profile.address,
            city=self.testuser.profile.city,
            postal_code=self.testuser.profile.postal_code,
            email=self.testuser.email,
            phone=self.testuser.profile.phone,
            documents=doc,
        )
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.patch(
                self.view_url,
                data={
                    "email": "new@mail.com",
                    "address": "new address",
                    "phone": "0000000000",
                },
                content_type="application/json",
            )
            assert response.status_code == 200, response
            member.refresh_from_db()
            self.testuser.refresh_from_db()
            assert member.email == self.testuser.email
            assert member.phone == self.testuser.profile.phone
            assert member.address == self.testuser.profile.address
            assert member.email == "new@mail.com"

    def test_delete_permissions(self):
        """Tested last because it (obviously) deletes users used in tests."""
        assert self.users_have_permission(
            method="delete",
            user_status=204,
            superuser_status=204,
        )

    def test_delete_kdance_impossible(self):
        """Tests that automatic superuser kdance cannot be deleted."""
        superuser = User.objects.get(username=settings.SUPERUSER_EMAIL)
        with AuthenticatedAction(self.client, superuser):
            response = self.client.delete(self.view_url)
            assert response.status_code == 401


@pytest.mark.django_db
class TestUserMePasswordView(AuthTestCase):
    view_url = reverse("api-user-me-password")
    view_function = UserMeApiViewSet

    _tmp_user: User | None = None
    _PASSWORD = "M0nSup3rM0tdePass3"

    @pytest.fixture(autouse=True)
    def set_tmp_user(self):
        tmp_user, _ = User.objects.get_or_create(
            username="tmpuser", email="tmp@mail.fr"
        )
        tmp_user.set_password(self._PASSWORD)
        tmp_user.save()
        self._tmp_user = tmp_user

    @parameterized.expand(
        [
            ("get", 405, 405),
            ("post", 405, 405),
            ("put", 400, 400),
            ("patch", 405, 405),
            ("delete", 405, 405),
        ]
    )
    def test_permissions(self, method, user_status, superuser_status):
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    @parameterized.expand(
        [
            "get",
            "post",
            "put",
            "patch",
            "delete",
        ]
    )
    def test_authentication_mandatory(self, method):
        assert self.anonymous_has_permission(method, 403)

    def test_put(self):
        with AuthenticatedAction(self.client, self._tmp_user):
            response = self.client.put(
                self.view_url,
                data={
                    "old_password": self._PASSWORD,
                    "new_password": "SuperM0tdePass3Auss1",
                },
                content_type="application/json",
            )
            assert response.status_code == 204, response

    @parameterized.expand(
        [
            (
                "Oupsy",
                "SuperM0tdePass3Auss1",
                "old_password",
                "Mot de passe actuel invalide.",
            ),
            (
                None,
                "tr0c0ur7",
                "new_password",
                "Votre mot de passe doit contenir au moins 12 caractères.",
            ),
            ("", "SuperM0tdePass3Auss1", "old_password", "Ce champ ne peut être vide."),
            (None, "", "new_password", "Ce champ ne peut être vide."),
        ]
    )
    def test_put_payload_error(self, old_pwd, new_pwd, key, message):
        old_pwd = old_pwd if old_pwd is not None else self._PASSWORD
        with AuthenticatedAction(self.client, self._tmp_user):
            response = self.client.put(
                self.view_url,
                data={"old_password": old_pwd, "new_password": new_pwd},
                content_type="application/json",
            )
            assert response.status_code == 400, response
            assert message in response.json()[key]
