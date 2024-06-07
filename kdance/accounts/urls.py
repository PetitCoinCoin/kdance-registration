from django.urls import include, path
from rest_framework import routers

from accounts.api.views import AuthApiViewSet, UsersApiViewSet, UsersMeApiViewSet
from accounts.views import SignUpView, login_user


router = routers.DefaultRouter()
router.register("auth", AuthApiViewSet, basename="api-auth")
router.register("users", UsersApiViewSet, basename="api-users")
router.register("users/me", UsersMeApiViewSet, basename="api-users-me")

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", login_user, name="login"),
    path("api/", include(router.urls)),
]
