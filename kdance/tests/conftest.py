from unittest.mock import Mock
import pytest

from django.contrib.auth.models import User
from members.models import (
    Course,
    Documents,
    Member,
    Season,
)
from tests.data_tests import (
    COURSE,
    MEMBER,
    SEASON,
    TESTUSER,
)


class CawlMock(Mock):
    def merchant(*a, **k):
        return Mock()


@pytest.fixture(autouse=True)
def mock_cawl(monkeypatch):
    monkeypatch.setattr(
        "onlinepayments.sdk.factory.Factory.create_client_from_configuration",
        lambda *a, **k: CawlMock(*a, **k),
    )


@pytest.fixture()
def mock_season() -> Season:
    season, _ = Season.objects.get_or_create(
        **SEASON,
        year="1900-1901",
    )
    return season


@pytest.fixture()
def mock_course(mock_season) -> Course:
    course, _ = Course.objects.get_or_create(
        **COURSE,
        season=mock_season,
    )
    return course


@pytest.fixture()
def mock_member(mock_season) -> Member:
    doc, _ = Documents.objects.get_or_create(
        authorise_photos=False,
        authorise_emergency=False,
    )
    member, _ = Member.objects.get_or_create(
        **MEMBER,
        user=User.objects.get(username=TESTUSER),
        season=mock_season,
        documents=doc,
    )
    return member
