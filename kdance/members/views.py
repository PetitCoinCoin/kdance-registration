from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


@login_required(login_url="login/")
def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, "pages/index_super.html", context={"user": request.user})
        return render(request, "pages/index.html", context={"user": request.user})

@login_required(login_url="login/")
def course_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated and request.user.is_superuser:
        return render(request, "pages/course_mgmt.html", context={"user": request.user})

@login_required(login_url="login/")
def member_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated and request.user.is_superuser:
        return render(request, "pages/member_mgmt.html", context={"user": request.user})

@login_required(login_url="login/")
def list_dl(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated and request.user.is_superuser:
        return render(request, "pages/list_dl.html", context={"user": request.user})
