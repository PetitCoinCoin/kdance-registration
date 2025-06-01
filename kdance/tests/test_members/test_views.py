"""Tests related to members views."""

from typing import Callable

import pytest
from django.http import QueryDict
from django.urls import reverse
from parameterized import parameterized

from members.views import (
    about,
    admin_mgmt,
    course_mgmt,
    download_pdf,
    index,
    list_dl,
    member,
    member_mgmt,
    site_mgmt,
    super_index,
    user_delete,
    user_edit,
    user_edit_pwd,
)
from tests.authentication import AuthenticatedAction, AuthTestCase


LOGIN_REDIRECT_PREFIX = "/login/?next="


class MembersViewsTestCase(AuthTestCase):
    """Tests all non API views from members app."""

    __test__ = False

    view_url: str
    view_function: Callable
    ADMIN_ONLY: bool

    @pytest.fixture(autouse=True)
    def setup_season(self, mock_season):
        pass

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


class TestMemberView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("member")
    view_function = member
    ADMIN_ONLY = False


class TestUserDeleteView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("user_delete")
    view_function = user_delete
    ADMIN_ONLY = False


class TestUserEdiddView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("user_edit")
    view_function = user_edit
    ADMIN_ONLY = False


class TestUserEditPwdView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("user_edit_pwd")
    view_function = user_edit_pwd
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


class TestSiteMgmtView(MembersViewsTestCase):
    __test__ = True
    view_url = reverse("site_mgmt")
    view_function = site_mgmt
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


class TestDownloadView(MembersViewsTestCase):
    __test__ = True
    view_function = download_pdf
    ADMIN_ONLY = False
    __doc: str = "attestation-sur-honneur-kdance"

    @property
    def view_url(self) -> str:
        query_dictionary = QueryDict(mutable=True)
        query_dictionary["doc"] = self.__doc
        return f"{reverse('download')}?{query_dictionary.urlencode()}"

    def test_login_redirection(self):
        response = self.client.get(self.view_url)
        assert response.status_code == 302
        assert response.url.startswith(LOGIN_REDIRECT_PREFIX)

    def test_no_file_requested(self):
        self.__doc = ""
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 404

    def test_file_does_not_exist(self):
        self.__doc = "hoho"
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 404


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
