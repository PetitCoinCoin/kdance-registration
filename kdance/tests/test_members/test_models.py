from unittest.mock import patch

import pytest

from django.contrib.auth.models import User
from parameterized import parameterized
from members.models import (
    Course,
    GeneralSettings,
    Payment,
    Season,
)
from tests.data_tests import (
    COURSE,
    SEASON,
    TESTUSER,
    TESTUSER_EMAIL,
)


@pytest.mark.django_db
def test_delete_old_seasons():
    for i in range(Season.SEASON_COUNT):
        Season.objects.create(
            year=f"190{i}-190{i + 1}",
            ffd_a_amount=0,
            ffd_b_amount=0,
            ffd_c_amount=0,
            ffd_d_amount=0,
        )
    assert Season.objects.count() == Season.SEASON_COUNT
    assert Season.objects.first().year == "1900-1901"
    season = Season(
        year="2000-2001",
        ffd_a_amount=0,
        ffd_b_amount=0,
        ffd_c_amount=0,
        ffd_d_amount=0,
    )
    season.save()
    assert Season.objects.count() == Season.SEASON_COUNT
    assert Season.objects.last().year == season.year
    assert Season.objects.first().year == "1901-1902"


@pytest.mark.django_db
def test_season_create_payment():
    testuser = User.objects.create(username=TESTUSER, email=TESTUSER_EMAIL)
    assert not Season.objects.count()
    assert not Payment.objects.count()
    Season.objects.create(
        year="1900-1901",
        ffd_a_amount=0,
        ffd_b_amount=0,
        ffd_c_amount=0,
        ffd_d_amount=0,
    )
    assert Season.objects.count() == 1
    assert Payment.objects.count() == 1
    assert Payment.objects.first().user == testuser


@parameterized.expand([True, False])
@patch.object(Course, "update_queue")
@pytest.mark.django_db
def test_manage_waiting_list(can_add_member, update):
    season = Season.objects.create(**SEASON, year="1900-1901")
    Course.objects.create(
        **COURSE,
        season=season,
    )
    gen_settings = GeneralSettings.get_solo()
    gen_settings.allow_new_member = can_add_member
    gen_settings.save()
    Course.objects.manage_waiting_lists()
    assert update.called is can_add_member
