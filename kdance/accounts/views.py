from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

def login_user(request):
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
            message = "Mauvais username ou mot de passe. La connexion a échoué."
            return render(request, "registration/login.html", context={"error": message})
    else:
        return render(request, "registration/login.html", context={"error": None})

def logout_view(request):
    logout(request)
    return redirect("index")
