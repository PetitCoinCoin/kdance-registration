from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


@login_required(login_url="login/")
def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        # si superuser, autre template
        return render(request, "pages/index.html", context={"user": request.user})
