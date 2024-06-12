from django.urls import include, path
from rest_framework import routers

from members.api.views import (
    CourseViewSet,
    MemberViewSet,
    SeasonViewSet,
    TeacherViewSet,
)
from members.views import index


router = routers.DefaultRouter()
router.register(r"courses", CourseViewSet, basename="api-courses")
router.register(r"members", MemberViewSet, basename="api-members")
router.register(r"seasons", SeasonViewSet, basename="api-seasons")
router.register(r"teachers", TeacherViewSet, basename="api-teachers")

urlpatterns = [
    path("", index, name="index"),
    path("api/", include(router.urls)),
]
