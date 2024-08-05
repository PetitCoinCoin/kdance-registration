import pytest

from django.contrib.auth.models import User
from rest_framework.test import APIClient


TESTUSER_EMAIL = "test@kdance.com"
TESTSUPERUSER_EMAIL = "testsuper@kdance.com"


@pytest.fixture
def api_client():
   return APIClient()

@pytest.fixture
def test_user():
   return User.objects.create(username="testuser", email=TESTUSER_EMAIL)

@pytest.fixture
def test_superuser():
   return User.objects.create_superuser(username="testsuperuser", email=TESTSUPERUSER_EMAIL)
