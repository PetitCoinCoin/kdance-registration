"""Tests related to Password API view."""
import pytest

from datetime import datetime, timedelta, timezone
from hashlib import sha512
from secrets import token_urlsafe
from unittest.mock import patch

from django.urls import reverse
from accounts.models import ResetPassword

from tests.conftest import TESTUSER_EMAIL, TESTSUPERUSER_EMAIL


@pytest.mark.django_db
class TestPasswordResetView:
    view_url = reverse('api-password-reset')

    @pytest.mark.parametrize(
        ("email", "status_code", "expected_count"),
        [
            ("plip@plop.fr", 404, 0),
            (TESTUSER_EMAIL, 202, 1),
            (TESTSUPERUSER_EMAIL, 202, 1),
        ],
    )
    def test_reset_password(
        self,
        email, status_code, expected_count,
        test_user, test_superuser, mailoutbox, api_client):
        assert ResetPassword.objects.count() == 0
        response = api_client.post(self.view_url, data={"email": email})
        assert response.status_code == status_code
        assert ResetPassword.objects.count() == expected_count
        assert len(mailoutbox) == expected_count
        if expected_count:
            mail = mailoutbox[0]
            assert mail.subject == "Réinitialisation du mot de passe K'Dance"
            assert list(mail.to) == [email]

    def test_reset_password_no_payload(self, mailoutbox, api_client):
        assert ResetPassword.objects.count() == 0
        response = api_client.post(self.view_url, data={})
        assert response.status_code == 400
        assert "email" in response.json().keys()
        assert ResetPassword.objects.count() == 0
        assert len(mailoutbox) == 0

    def test_reset_password_get(self, api_client):
        response = api_client.get(self.view_url)
        assert response.status_code == 405

    def test_reset_password_put(self, api_client):
        response = api_client.put(self.view_url, data={})
        assert response.status_code == 405

    def test_reset_password_patch(self, api_client):
        response = api_client.patch(self.view_url, data={})
        assert response.status_code == 405

    def test_reset_password_delete(self, api_client):
        response = api_client.delete(self.view_url)
        assert response.status_code == 405


@pytest.mark.django_db
class TestPasswordNewView:
    view_url = reverse('api-password-new')
    _token: str

    @pytest.fixture(autouse=True)
    def set_pwd_reset(self, test_user):
        token = token_urlsafe()
        ResetPassword(
            user=test_user,
            request_hash=sha512(token.encode()).hexdigest(),
        ).save()
        self._token = token
        assert ResetPassword.objects.count() == 1

    def test_new_password(self, test_user, api_client):
        new_pwd = "SuperMotDePasse0"
        response = api_client.post(
            self.view_url,
            data={
                "email": test_user.email,
                "password": new_pwd,
                "token": self._token,

            },
        )
        assert response.status_code == 200
        assert ResetPassword.objects.count() == 0
        test_user.refresh_from_db()
        assert test_user.check_password(new_pwd)
        assert test_user.is_authenticated is True

    @pytest.mark.parametrize(
        ("email", "password", "token", "error_key", "message"),
        [
            ("plip@plop.fr", "SuperMotDePasse0", True, "email", "Email incorrect, cet utilisateur n'existe pas."),
            (TESTSUPERUSER_EMAIL, "SuperMotDePasse0", True, "email", "Email incorrect, aucune demande de réinitialisation trouvée."),
            (TESTUSER_EMAIL, "SuperMotDePasse0", False, "token", "Lien de réinitialisation incorrect pour cet utilisateur."),
            (TESTUSER_EMAIL, "nul", True, "password", "Votre mot de passe doit contenir au moins 12 caractères."),
        ],
    )
    def test_new_password_payload_error(
        self,
        email, password, token, error_key, message,
        test_superuser, api_client,
    ):
        response = api_client.post(
            self.view_url,
            data={
                "email": email,
                "password": password,
                "token": self._token if token else "plop",

            },
        )
        assert response.status_code == 400
        assert error_key in response.json().keys()
        assert message in response.json()[error_key]
        assert ResetPassword.objects.count() == 1

    @patch("accounts.api.serializers.timezone.now")
    def test_new_password_token_expired(self, now, api_client):
        now.return_value = datetime.now(timezone.utc) + timedelta(minutes=35)
        response = api_client.post(
            self.view_url,
            data={
                "email": TESTUSER_EMAIL,
                "password": "SuperMotdePasse0",
                "token": self._token,

            },
        )
        assert response.status_code == 400
        assert "token" in response.json().keys()
        assert "Lien de réinitialisation expiré. Veuillez refaire une demande de réinitialisation." in response.json()["token"]
        assert ResetPassword.objects.count() == 1

    def test_new_password_get(self, api_client):
        response = api_client.get(self.view_url)
        assert response.status_code == 405

    def test_new_password_put(self, api_client):
        response = api_client.put(self.view_url, data={})
        assert response.status_code == 405

    def test_new_password_patch(self, api_client):
        response = api_client.patch(self.view_url, data={})
        assert response.status_code == 405

    def test_new_password_delete(self, api_client):
        response = api_client.delete(self.view_url)
        assert response.status_code == 405
