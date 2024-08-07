from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


@login_required()
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/index.html", context={"user": request.user})

@login_required()
def super_index(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(request, "pages/index_super.html", context={"user": request.user})
    raise PermissionDenied

@login_required()
def course_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(request, "pages/course_mgmt.html", context={"user": request.user})
    raise PermissionDenied

@login_required()
def member_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(request, "pages/member_mgmt.html", context={"user": request.user})
    raise PermissionDenied

@login_required()
def admin_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(request, "pages/admin_mgmt.html", context={"user": request.user})
    raise PermissionDenied

@login_required()
def list_dl(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(request, "pages/list_dl.html", context={"user": request.user})
    raise PermissionDenied

def about(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/about.html", context={"user": request.user})
