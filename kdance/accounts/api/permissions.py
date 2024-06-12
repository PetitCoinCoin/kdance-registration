from django.http import HttpRequest
from django.views import View
from rest_framework.permissions import BasePermission

class SuperUserPermission(BasePermission):
    def has_permission(self, request: HttpRequest, _: View) -> bool:
        if request.user and request.user.is_authenticated:
            if request.user.is_superuser or request.path.startswith(f"/api/user/me"):
                return True
            if request.method == "GET" and not request.path.startswith("/api/users") and not request.path.startswith("/api/members"):
                return True
        if request.method == "POST" and request.path.startswith("/api/users/") or request.path.startswith("/api/members/"):
            return True
        return False
