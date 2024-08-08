"""Utilities to test as an authenticated user."""
import logging

from typing import Any

from django.contrib.auth.models import User
from django.test import Client, TestCase
from rest_framework.test import APIClient

from accounts.models import Profile
from tests.data_tests import (
    SUPERTESTUSER,
    SUPERTESTUSER_EMAIL,
    TESTUSER,
    TESTUSER_EMAIL,
)

_logger = logging.getLogger(__name__)


class AuthenticatedAction:
    def __init__(self, client: Client, user: User) -> None:
        self.client = client
        self.user = user

    def __enter__(self):
        self.client.force_login(self.user)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.logout()


class AuthTestCase(TestCase):
    view_url: str | None = None
    view_function: Any = None

    @classmethod
    def setUpTestData(cls):
        cls.testuser = User.objects.create(username=TESTUSER, email=TESTUSER_EMAIL)
        Profile(user=cls.testuser, address="Ici", phone="0123456789").save()
        cls.super_testuser = User.objects.create_superuser(username=SUPERTESTUSER, email=SUPERTESTUSER_EMAIL)
        Profile(user=cls.super_testuser, address="Là", phone="0123456789").save()
        cls.client = APIClient()

    def users_have_permission(
        self,
        method: str,
        user_status: int,
        superuser_status: int,
        urls: list[tuple] | tuple | None = None,
        **kwargs,
    ) -> bool:
        if urls is None:
            assert self.view_url is not None
            assert self.view_function is not None
            urls = [(self.view_url, self.view_function)]
        elif not isinstance(urls, list):
            urls = [urls]
        for url, view in urls:
            # Simple user
            with AuthenticatedAction(self.client, self.testuser):
                response = getattr(self.client, method)(url, **kwargs)
                _logger.debug("testuser response: %s", response)
                if response.status_code != user_status:
                    return False
                _logger.debug(response.resolver_match.func)
                if response.resolver_match.func.__name__ != view.__name__:
                    return False
            # Super user
            with AuthenticatedAction(self.client, self.super_testuser):
                response = getattr(self.client, method)(url, **kwargs)
                _logger.debug("super testuser response: %s", response)
                if response.status_code != superuser_status:
                    return False
        return True

    def anonymous_has_permission(
        self,
        method: str,
        status: int,
        urls: list[str] | str | None = None,
        **kwargs
    ) -> bool:
        if urls is None:
            assert self.view_url is not None
            urls = [self.view_url]
        elif not isinstance(urls, list):
            urls = [urls]
        for url in urls:
            response = getattr(self.client, method)(url, **kwargs)
            _logger.debug("without auth response: %s", response)
            if response.status_code != status:
                return False
        return True
