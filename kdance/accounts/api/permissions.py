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

from django.http import HttpRequest
from django.views import View
from rest_framework.permissions import BasePermission


class SuperUserPermission(BasePermission):
    """Handle permissions between simple and super users.
    Note: not being authenticated if need should raise 401 instead of 403 > TODO.
    """

    def has_permission(self, request: HttpRequest, _: View) -> bool:
        if request.user and request.user.is_authenticated:
            if request.user.is_superuser or request.path.startswith("/api/user/me"):
                return True
            if request.method == "GET" and not (
                request.path.startswith("/api/users")
                or request.path.startswith("/api/members")
                or request.path.startswith("/api/payments")
                or request.path.startswith("/api/checks")
            ):
                return True
            if request.method != "PUT" and request.path.startswith("/api/members/"):
                return True
        if (
            (request.method == "POST" and request.path.startswith("/api/users/"))
            or request.path.startswith("/api/password/")
            or (request.method == "GET" and request.path.startswith("/api/settings"))
        ):
            return True
        return False
