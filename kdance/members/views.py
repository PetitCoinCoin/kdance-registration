from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


def _is_teacher(request: HttpRequest) -> bool:
    return request.user.groups.filter(name=settings.TEACHER_GROUP_NAME).exists()


@require_http_methods(["GET"])
@login_required()
def index(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/index.html",
        context={"user": request.user, "is_teacher": _is_teacher(request)},
    )


@require_http_methods(["GET"])
@login_required()
def super_index(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser or _is_teacher(request):
        return render(
            request,
            "pages/index_super.html",
            context={
                "user": request.user,
                "is_teacher": _is_teacher(request),
            },
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def course_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/course_mgmt.html",
            context={"user": request.user, "is_teacher": _is_teacher(request)},
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def member_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/member_mgmt.html",
            context={"user": request.user, "is_teacher": _is_teacher(request)},
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def admin_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/admin_mgmt.html",
            context={"user": request.user, "is_teacher": _is_teacher(request)},
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def site_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/site_mgmt.html",
            context={"user": request.user, "is_teacher": _is_teacher(request)},
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def list_dl(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/list_dl.html",
            context={"user": request.user, "is_teacher": _is_teacher(request)},
        )
    raise PermissionDenied


@require_http_methods(["GET"])
def about(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/about.html",
        context={"user": request.user, "is_teacher": _is_teacher(request)},
    )
