"""Tests related to General Settings API view."""

import pytest

from django.urls import reverse
from parameterized import parameterized

from members.api.views import GeneralSettingsViewSet
from tests.authentication import AuthTestCase


@pytest.mark.django_db
class TestGeneralSettingsApiView(AuthTestCase):
    view_function = GeneralSettingsViewSet
    view_url = reverse("api-settings-detail")

    @parameterized.expand(
        [
            ("get", 200, 200),
            ("post", 403, 405),
            ("put", 403, 200),
            ("patch", 403, 405),
            ("delete", 403, 405),
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
            ("get", 200),
            ("post", 403),
            ("put", 403),
            ("patch", 403),
            ("delete", 403),
        ]
    )
    def test_authentication_mandatory(self, method, code):
        assert self.anonymous_has_permission(method, code)
