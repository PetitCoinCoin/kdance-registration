from django.urls import include, path
from rest_framework import routers

from members.api.views import (
    CourseViewSet,
    MemberViewSet,
    SeasonViewSet,
    TeacherViewSet,
)
from members.views import (
    course_mgmt,
    index,
    list_dl,
    member_mgmt,
)


router = routers.DefaultRouter()
router.register(r"courses", CourseViewSet, basename="api-courses")
router.register(r"members", MemberViewSet, basename="api-members")
router.register(r"seasons", SeasonViewSet, basename="api-seasons")
router.register(r"teachers", TeacherViewSet, basename="api-teachers")

urlpatterns = [
    path("", index, name="index"),
    path("course_mgmt", course_mgmt, name="course_mgmt"),
    path("member_mgmt", member_mgmt, name="member_mgmt"),
    path("list_dl", list_dl, name="list_dl"),
    path("api/", include(router.urls)),
]
