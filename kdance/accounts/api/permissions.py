from django.http import HttpRequest
from django.views import View
from rest_framework.permissions import BasePermission

class SuperUserPermission(BasePermission):
    def has_permission(self, request: HttpRequest, _: View) -> bool:
        if request.user.is_superuser or request.path.startswith(f"/api/users/me/{request.user.pk}"):
            return True
        if request.method == "GET" and not request.path.startswith("/api/users/me"):
            return True
        return False
