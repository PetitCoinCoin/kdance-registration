from django.contrib.auth import login, logout, authenticate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render


def signup_view(request: HttpRequest) -> HttpResponse:
    return render(request, "registration/signup.html")

def login_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    message = ""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            message = "Email et/ou mot de passe incorrect(s). La connexion a échoué."
            return render(request, "registration/login.html", context={"error": message})
    else:
        return render(request, "registration/login.html", context={"error": None})

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("index")
