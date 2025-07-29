"""
Copyright 2024, 2025 Andréa Marnier

This file is part of KDance registration.

KDance registration is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by the
Free Software Foundation, either version 3 of the License, or any later version.

KDance registration is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
for more details.

You should have received a copy of the GNU Affero General Public License along
with KDance registration. If not, see <https://www.gnu.org/licenses/>.
"""

from django.urls import include, path
from rest_framework import routers

from members.api.views import (
    CheckViewSet,
    CourseViewSet,
    GeneralSettingsViewSet,
    MemberViewSet,
    PaymentViewSet,
    SeasonViewSet,
    TeacherViewSet,
)
from members.views import (
    about,
    admin_mgmt,
    checkout,
    course_mgmt,
    download_pdf,
    index,
    list_dl,
    member,
    member_mgmt,
    online_checkout,
    session_status,
    site_mgmt,
    super_index,
    user_delete,
    user_edit,
    user_edit_pwd,
)


class SingletonRouter(routers.SimpleRouter):
    routes = [
        routers.Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={
                "get": "retrieve",
                "put": "update",
            },
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
    ]


router = routers.DefaultRouter()
router.register(r"checks", CheckViewSet, basename="api-checks")
router.register(r"courses", CourseViewSet, basename="api-courses")
router.register(r"members", MemberViewSet, basename="api-members")
router.register(r"payments", PaymentViewSet, basename="api-payments")
router.register(r"seasons", SeasonViewSet, basename="api-seasons")
router.register(r"teachers", TeacherViewSet, basename="api-teachers")

singleton_router = SingletonRouter()
singleton_router.register(r"settings", GeneralSettingsViewSet, "api-settings")

urlpatterns = [
    path("", index, name="index"),
    path("download-pdf/", download_pdf, name="download"),
    path("checkout", checkout, name="checkout"),
    path("online_checkout", online_checkout, name="online_checkout"),
    path("session_status/", session_status, name="session_status"),
    path("user_edit", user_edit, name="user_edit"),
    path("user_edit_pwd", user_edit_pwd, name="user_edit_pwd"),
    path("user_delete", user_delete, name="user_delete"),
    path("member", member, name="member"),
    path("about", about, name="about"),
    path("super", super_index, name="super_index"),
    path("super/admin_mgmt/", admin_mgmt, name="admin_mgmt"),
    path("super/course_mgmt/", course_mgmt, name="course_mgmt"),
    path("super/member_mgmt/", member_mgmt, name="member_mgmt"),
    path("super/site_mgmt/", site_mgmt, name="site_mgmt"),
    path("super/list_dl/", list_dl, name="list_dl"),
    path("api/", include(router.urls)),
    path("api/", include(singleton_router.urls)),
]
