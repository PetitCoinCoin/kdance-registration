from django.urls import include, path
from rest_framework import routers

from members.api.views import (
    CheckViewSet,
    CourseViewSet,
    MemberViewSet,
    PaymentViewSet,
    SeasonViewSet,
    TeacherViewSet,
)
from members.views import (
    course_mgmt,
    index,
    list_dl,
    member_mgmt,
    super_index,
)


router = routers.DefaultRouter()
router.register(r"checks", CheckViewSet, basename="api-checks")
router.register(r"courses", CourseViewSet, basename="api-courses")
router.register(r"members", MemberViewSet, basename="api-members")
router.register(r"payments", PaymentViewSet, basename="api-payments")
router.register(r"seasons", SeasonViewSet, basename="api-seasons")
router.register(r"teachers", TeacherViewSet, basename="api-teachers")

urlpatterns = [
    path("", index, name="index"),
    path("super", super_index, name="super_index"),
    path("super/course_mgmt", course_mgmt, name="course_mgmt"),
    path("super/member_mgmt", member_mgmt, name="member_mgmt"),
    path("super/list_dl", list_dl, name="list_dl"),
    path("api/", include(router.urls)),
]
