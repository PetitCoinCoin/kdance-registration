from django.contrib.auth import login, logout, authenticate
from django.http import Http404, HttpRequest, HttpResponse
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
            return redirect("super_index" if user.is_superuser else "index")
        else:
            message = "Utilisateur et/ou mot de passe incorrect(s). La connexion a échoué."
            return render(request, "registration/login.html", context={"error": message})
    else:
        return render(request, "registration/login.html", context={"error": None})

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("index")

def password_reset_view(request) -> HttpResponse:
    return render(request, "pages/pwd_reset.html")

def password_new_view(request) -> HttpResponse:
    if not request.GET.get("token"):
        raise Http404
    return render(request, "pages/pwd_new.html")
