"""Tests related to Password API view."""

import pytest

from datetime import datetime, timedelta, timezone
from hashlib import sha512
from secrets import token_urlsafe
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from parameterized import parameterized

from accounts.models import ResetPassword
from accounts.api.views import PasswordApiViewSet
from tests.authentication import AuthTestCase
from tests.data_tests import TESTUSER_EMAIL, SUPERTESTUSER_EMAIL


@pytest.mark.django_db
class TestPasswordResetView(AuthTestCase):
    view_url = reverse("api-password-reset")
    view_function = PasswordApiViewSet

    @parameterized.expand(
        [
            ("get", 405, 405),
            ("post", 400, 400),
            ("put", 405, 405),
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
            (TESTUSER_EMAIL, False),
            (SUPERTESTUSER_EMAIL, False),
            ("TesT@KDance.COM", False),
            (TESTUSER_EMAIL, True),
        ]
    )
    def test_reset_password(self, email, exists_already):
        assert ResetPassword.objects.count() == 0
        if exists_already:
            user = User.objects.get(email=TESTUSER_EMAIL)
            ResetPassword.objects.create(user=user, request_hash="somehash")
        response = self.client.post(self.view_url, data={"email": email})
        assert response.status_code == 202, response
        assert ResetPassword.objects.count() == 1
        assert len(mail.outbox) == 1
        email_sent = mail.outbox[0]
        assert email_sent.subject == "Réinitialisation du mot de passe K'Dance"
        assert list(email_sent.to) == [email.lower()]

    @parameterized.expand(
        [
            (None, "Ce champ est obligatoire."),
            ("", "Ce champ ne peut être vide."),
            ("plop@plip.com", "Email incorrect, cet utilisateur n'existe pas."),
        ]
    )
    def test_reset_password_error(self, email, message):
        data = {}
        if email is not None:
            data["email"] = email
        assert ResetPassword.objects.count() == 0
        response = self.client.post(self.view_url, data=data)
        assert response.status_code == 400, response
        assert message in response.json()["email"]
        assert ResetPassword.objects.count() == 0
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestPasswordNewView(AuthTestCase):
    view_url = reverse("api-password-new")
    view_function = PasswordApiViewSet
    _token: str

    @pytest.fixture(autouse=True)
    def set_pwd_reset(self):
        token = token_urlsafe()
        reset_pwd, _ = ResetPassword.objects.get_or_create(
            user=self.testuser,
        )
        reset_pwd.request_hash = sha512(token.encode()).hexdigest()
        reset_pwd.save()
        self._token = token
        assert ResetPassword.objects.count() == 1

    @parameterized.expand(
        [
            ("get", 405, 405),
            ("post", 400, 400),
            ("put", 405, 405),
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

    @parameterized.expand([TESTUSER_EMAIL, "TesT@KDance.COM"])
    def test_new_password(self, email):
        new_pwd = "SuperMotDePasse0"
        response = self.client.post(
            self.view_url,
            data={
                "email": email,
                "password": new_pwd,
                "token": self._token,
            },
        )
        assert response.status_code == 200, response
        assert ResetPassword.objects.count() == 0
        self.testuser.refresh_from_db()
        assert self.testuser.check_password(new_pwd)

    @parameterized.expand(
        [
            (
                "plip@plop.fr",
                "SuperMotDePasse0",
                True,
                "email",
                "Email incorrect, cet utilisateur n'existe pas.",
            ),
            (
                SUPERTESTUSER_EMAIL,
                "SuperMotDePasse0",
                True,
                "email",
                "Email incorrect, aucune demande de réinitialisation trouvée.",
            ),
            (
                TESTUSER_EMAIL,
                "SuperMotDePasse0",
                False,
                "token",
                "Lien de réinitialisation incorrect pour cet utilisateur.",
            ),
            (
                TESTUSER_EMAIL,
                "nul",
                True,
                "password",
                "Votre mot de passe doit contenir au moins 12 caractères.",
            ),
        ]
    )
    def test_new_password_payload_error(
        self,
        email,
        password,
        token,
        error_key,
        message,
    ):
        response = self.client.post(
            self.view_url,
            data={
                "email": email,
                "password": password,
                "token": self._token if token else "plop",
            },
        )
        assert response.status_code == 400, response
        assert error_key in response.json().keys()
        assert message in response.json()[error_key]
        assert ResetPassword.objects.count() == 1

    @patch("accounts.api.serializers.timezone.now")
    def test_new_password_token_expired(self, now):
        now.return_value = datetime.now(timezone.utc) + timedelta(minutes=35)
        response = self.client.post(
            self.view_url,
            data={
                "email": TESTUSER_EMAIL,
                "password": "SuperMotdePasse0",
                "token": self._token,
            },
        )
        assert response.status_code == 400, response
        assert "token" in response.json().keys()
        assert (
            "Lien de réinitialisation expiré. Veuillez refaire une demande de réinitialisation."
            in response.json()["token"]
        )
        assert ResetPassword.objects.count() == 1
