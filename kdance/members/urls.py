from django.urls import include, path
from rest_framework import routers

from members.api.views import (
    CheckViewSet,
    CourseViewSet,
    GeneralSettingsViewSet,
    MemberViewSet,
    PaymentViewSet,
    SeasonViewSet,
    TeacherViewSet,
)
from members.views import (
    about,
    admin_mgmt,
    course_mgmt,
    user_edit,
    index,
    list_dl,
    member_mgmt,
    site_mgmt,
    super_index,
)


class SingletonRouter(routers.SimpleRouter):
    routes = [
        routers.Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={
                "get": "retrieve",
                "put": "update",
            },
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
    ]


router = routers.DefaultRouter()
router.register(r"checks", CheckViewSet, basename="api-checks")
router.register(r"courses", CourseViewSet, basename="api-courses")
router.register(r"members", MemberViewSet, basename="api-members")
router.register(r"payments", PaymentViewSet, basename="api-payments")
router.register(r"seasons", SeasonViewSet, basename="api-seasons")
router.register(r"teachers", TeacherViewSet, basename="api-teachers")

singleton_router = SingletonRouter()
singleton_router.register(r"settings", GeneralSettingsViewSet, "api-settings")

urlpatterns = [
    path("", index, name="index"),
    path("user_edit", user_edit, name="user_edit"),
    path("about", about, name="about"),
    path("super", super_index, name="super_index"),
    path("super/admin_mgmt/", admin_mgmt, name="admin_mgmt"),
    path("super/course_mgmt/", course_mgmt, name="course_mgmt"),
    path("super/member_mgmt/", member_mgmt, name="member_mgmt"),
    path("super/site_mgmt/", site_mgmt, name="site_mgmt"),
    path("super/list_dl/", list_dl, name="list_dl"),
    path("api/", include(router.urls)),
    path("api/", include(singleton_router.urls)),
]
