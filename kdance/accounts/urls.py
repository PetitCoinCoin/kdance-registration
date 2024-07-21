from django.urls import include, path
from rest_framework import routers

from accounts.api.views import UsersApiViewSet, UserMeApiViewSet
from accounts.views import login_view, signup_view


router = routers.DefaultRouter()
router.register("users", UsersApiViewSet, basename="api-users")

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("api/", include(router.urls)),
    path("api/user/me/", UserMeApiViewSet.as_view(actions={
        "get": "retrieve",
        "patch": "partial_update",
        "delete": "destroy"
    }), name="api-user-me"),
    path("api/user/me/password", UserMeApiViewSet.as_view(actions={
        "put": "password",
    }), name="api-user-me-password"),
    path("api/users/admin/<str:action>", UsersApiViewSet.as_view(actions={
        "put": "admin",
    }), name="api-users-admin"),
]
