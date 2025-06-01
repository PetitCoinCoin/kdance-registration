"""Tests related to accounts views."""

from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.urls import reverse
from parameterized import parameterized

from accounts.views import (
    login_view,
    password_new_view,
    password_reset_view,
    signup_view,
)
from tests.authentication import AuthenticatedAction, AuthTestCase


class TestLoginView(AuthTestCase):
    view_url = reverse("login")
    view_function = login_view

    @parameterized.expand(
        [
            ("get", 200),
            ("post", 200),
            ("put", 405),
            ("patch", 405),
            ("delete", 405),
        ]
    )
    def test_permissions(self, method, status):
        assert self.users_have_permission(
            method=method,
            user_status=status,
            superuser_status=status,
        )

    @parameterized.expand(["get", "post"])
    def test_authentication_not_mandatory(self, method):
        assert self.anonymous_has_permission(method=method, status=200)

    @parameterized.expand(
        [
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ]
    )
    def test_post_login_user_anonymous(self, is_superuser, remember_me):
        username = "plip"
        email = "plip@plop.fr"
        password = "M0nSup3rM0tdePass3"
        data = {"username": username, "password": password}
        if remember_me:
            data["remember"] = "y"
        if is_superuser:
            user = User.objects.create_superuser(username=username, email=email)
        else:
            user = User.objects.create(username=username, email=email)
        user.set_password(password)
        user.save()
        response = self.client.post(
            self.view_url,
            data=data,
        )
        assert response.status_code == 302
        assert (
            response.url == reverse("super_index") if is_superuser else reverse("index")
        )

    def test_post_login_user_authenticated(self):
        """Tests that if a login request is made by authenticated user, them will be logged out."""
        username = "plip"
        email = "plip@plop.fr"
        password = "M0nSup3rM0tdePass3"
        data = {"username": username, "password": password}
        user = User.objects.create_superuser(username=username, email=email)
        user.set_password(password)
        user.save()
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.post(
                self.view_url,
                data=data,
            )
            assert response.status_code == 302
            # Authenticated simple user logged in as super user
            assert response.url == reverse("super_index")

    def test_post_login_wrong_credentials(self):
        response = self.client.post(self.view_url)
        assert response.status_code == 200, response
        assert (
            response.context["error"]
            == "Utilisateur et/ou mot de passe incorrect(s). La connexion a échoué."
        )


class TestSignUpView(AuthTestCase):
    view_url = reverse("signup")
    view_function = signup_view

    @parameterized.expand(
        [
            ("get", 200),
            ("post", 405),
            ("put", 405),
            ("patch", 405),
            ("delete", 405),
        ]
    )
    def test_permissions(self, method, status):
        assert self.users_have_permission(
            method=method,
            user_status=status,
            superuser_status=status,
        )

    def test_authentication_not_mandatory(self):
        assert self.anonymous_has_permission(method="get", status=200)


class TestPasswordResetView(AuthTestCase):
    view_url = reverse("pwd_reset")
    view_function = password_reset_view

    @parameterized.expand(
        [
            ("get", 200),
            ("post", 405),
            ("put", 405),
            ("patch", 405),
            ("delete", 405),
        ]
    )
    def test_permissions(self, method, status):
        response = getattr(self.client, method)(self.view_url)
        assert response.status_code == status

    def test_redirection_with_auth(self):
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 302, response
            assert response.url == reverse("index")
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 302, response
            assert response.url == reverse("index")


class TestPasswordNewView(AuthTestCase):
    view_url = f"{reverse('pwd_new')}?{urlencode({'token': 'token'})}"
    view_function = password_new_view

    @parameterized.expand(
        [
            ("get", 200),
            ("post", 405),
            ("put", 405),
            ("patch", 405),
            ("delete", 405),
        ]
    )
    def test_permissions(self, method, status):
        assert self.users_have_permission(
            method=method,
            user_status=status,
            superuser_status=status,
        )

    def test_authentication_not_mandatory(self):
        assert self.anonymous_has_permission(method="get", status=200)

    def test_token_mandatory(self):
        response = self.client.get(reverse("pwd_new"))
        assert response.status_code == 404
