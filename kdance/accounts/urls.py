from django.urls import include, path
from rest_framework import routers

from accounts.api.views import (
    PasswordApiViewSet,
    UsersApiViewSet,
    UserMeApiViewSet,
)
from accounts.views import (
    login_view,
    password_new_view,
    password_reset_view,
    signup_view,
)


router = routers.DefaultRouter()
router.register("users", UsersApiViewSet, basename="api-users")

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("pwd_reset/", password_reset_view, name="pwd_reset"),
    path("pwd_new/", password_new_view, name="pwd_new"),
    path("api/", include(router.urls)),
    path("api/user/me/", UserMeApiViewSet.as_view(actions={
        "get": "retrieve",
        "patch": "partial_update",
        "delete": "destroy"
    }), name="api-user-me"),
    path("api/user/me/password/", UserMeApiViewSet.as_view(actions={
        "put": "password",
    }), name="api-user-me-password"),
    path("api/users/admin/<str:action>/", UsersApiViewSet.as_view(actions={
        "put": "admin",
    }), name="api-users-admin"),
    path("api/password/reset/", PasswordApiViewSet.as_view(actions={
        "post": "reset",
    }), name="api-password-reset"),
    path("api/password/new/", PasswordApiViewSet.as_view(actions={
        "post": "new",
    }), name="api-password-new"),
]
