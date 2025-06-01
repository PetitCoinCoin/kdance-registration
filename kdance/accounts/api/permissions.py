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
