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


@pytest.fixture(autouse=True)
def mock_stripe(monkeypatch):
    monkeypatch.setattr(
        "stripe.Product.create", lambda *a, **k: {"id": "stripe_product_id"}
    )
    monkeypatch.setattr(
        "stripe.Price.create", lambda *a, **k: {"id": "stripe_price_id"}
    )
    monkeypatch.setattr(
        "stripe.Price.modify", lambda *a, **k: {"id": "stripe_other_price_id"}
    )
    monkeypatch.setattr(
        "stripe.Coupon.create", lambda *a, **k: {"id": "stripe_coupon_id"}
    )
    monkeypatch.setattr(
        "stripe.checkout.Session.create",
        lambda *a, **k: {"client_secret": "session_secret"},
    )
    monkeypatch.setattr(
        "stripe.Price.create", lambda *a, **k: {"id": "stripe_price_id"}
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
