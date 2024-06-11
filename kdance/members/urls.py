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
router.register(r"courses", CourseViewSet)
router.register(r"members", MemberViewSet)
router.register(r"seasons", SeasonViewSet)
router.register(r"teachers", TeacherViewSet)

urlpatterns = [
    path("", index, name="index"),
    # path("", logout, name="logout"),
    path("api/", include(router.urls)),
]
