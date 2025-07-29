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

from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.http import Http404, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect, render


@require_http_methods(["GET"])
def signup_view(request: HttpRequest) -> HttpResponse:
    return render(request, "registration/signup.html")


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    message = ""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not request.POST.get("remember", ""):
                # session cookie will expire when the user’s web browser is closed.
                request.session.set_expiry(0)
            return redirect(
                "super_index"
                if user.is_superuser  # type: ignore[attr-defined]
                or request.user.groups.filter(name=settings.TEACHER_GROUP_NAME).exists()
                else "index"
            )
        else:
            message = (
                "Utilisateur et/ou mot de passe incorrect(s). La connexion a échoué."
            )
            return render(
                request, "registration/login.html", context={"error": message}
            )
    else:
        return render(request, "registration/login.html", context={"error": None})


@require_http_methods(["GET"])
def password_reset_view(request) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("index")
    return render(request, "pages/pwd_reset.html")


@require_http_methods(["GET"])
def password_new_view(request) -> HttpResponse:
    if not request.GET.get("token"):
        raise Http404
    return render(request, "pages/pwd_new.html")
