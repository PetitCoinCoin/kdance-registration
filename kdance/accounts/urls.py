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

from accounts.api.views import (
    PasswordApiViewSet,
    UsersApiViewSet,
    UserMeApiViewSet,
)
from accounts.views import (
    login_view,
    password_new_view,
    password_reset_view,
    signup_view,
)


router = routers.DefaultRouter()
router.register("users", UsersApiViewSet, basename="api-users")

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("pwd_reset/", password_reset_view, name="pwd_reset"),
    path("pwd_new/", password_new_view, name="pwd_new"),
    path("api/", include(router.urls)),
    path(
        "api/user/me/",
        UserMeApiViewSet.as_view(
            actions={"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="api-user-me",
    ),
    path(
        "api/user/me/password/",
        UserMeApiViewSet.as_view(
            actions={
                "put": "password",
            }
        ),
        name="api-user-me-password",
    ),
    path(
        "api/user/me/validate/",
        UserMeApiViewSet.as_view(
            actions={
                "put": "validate",
            }
        ),
        name="api-user-me-validate",
    ),
    path(
        "api/users/admin/<str:action>/",
        UsersApiViewSet.as_view(
            actions={
                "put": "admin",
            }
        ),
        name="api-users-admin",
    ),
    path(
        "api/users/teacher/<str:action>/",
        UsersApiViewSet.as_view(
            actions={
                "put": "teacher",
            }
        ),
        name="api-users-teacher",
    ),
    path(
        "api/password/reset/",
        PasswordApiViewSet.as_view(
            actions={
                "post": "reset",
            }
        ),
        name="api-password-reset",
    ),
    path(
        "api/password/new/",
        PasswordApiViewSet.as_view(
            actions={
                "post": "new",
            }
        ),
        name="api-password-new",
    ),
]
