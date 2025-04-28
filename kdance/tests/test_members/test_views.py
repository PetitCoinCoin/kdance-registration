"""Tests related to members views."""

from typing import Callable

import pytest
from django.urls import reverse
from parameterized import parameterized

from members.models import Season
from members.views import (
    about,
    admin_mgmt,
    course_mgmt,
    index,
    list_dl,
    member_mgmt,
    super_index,
)
from tests.authentication import AuthTestCase


LOGIN_REDIRECT_PREFIX = "/login/?next="


class MembersViewsTestCase(AuthTestCase):
    """Tests all non API views from members app."""

    __test__ = False

    view_url: str
    view_function: Callable
    ADMIN_ONLY: bool

    @pytest.fixture(autouse=True)
    def setup_season(self):
        Season.objects.get_or_create(
            year="1900-1901",
            ffd_a_amount=0,
            ffd_b_amount=0,
            ffd_c_amount=0,
            ffd_d_amount=0,
        )

    @parameterized.expand(["get", "post", "put", "patch", "delete"])
    def test_permissions(self, method):
        user_status = 405 if method != "get" else 403 if self.ADMIN_ONLY else 200
        superuser_status = 405 if method != "get" else 200
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    def test_login_redirection(self):
        response = self.client.get(self.view_url)
        assert response.status_code == 302
        assert response.url == LOGIN_REDIRECT_PREFIX + self.view_url


class TestIndexView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("index")
    view_function = index
    ADMIN_ONLY = False


class TestSuperIndexView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("super_index")
    view_function = super_index
    ADMIN_ONLY = True


class TestCourseMgmtView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("course_mgmt")
    view_function = course_mgmt
    ADMIN_ONLY = True


class TestAdminMgmtView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("admin_mgmt")
    view_function = admin_mgmt
    ADMIN_ONLY = True


class TestMemberMgmtView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("member_mgmt")
    view_function = member_mgmt
    ADMIN_ONLY = True


class TestListDLView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("list_dl")
    view_function = list_dl
    ADMIN_ONLY = True


class TestAboutView(AuthTestCase):
    view_url = reverse("about")
    view_function = about

    @parameterized.expand(["get", "post", "put", "patch", "delete"])
    def test_permissions(self, method):
        status = 405 if method != "get" else 200
        assert self.users_have_permission(
            method=method,
            user_status=status,
            superuser_status=status,
        )

    def test_authentication_not_mandatory(self):
        assert self.anonymous_has_permission(
            method="get",
            status=200,
        )
