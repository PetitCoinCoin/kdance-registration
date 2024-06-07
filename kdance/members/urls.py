from django.urls import include, path
from rest_framework import routers

from members.api.views import (
    CourseViewSet,
    SeasonViewSet,
    TeacherViewSet,
)
from members.views import index


router = routers.DefaultRouter()
router.register(r"course", CourseViewSet)
router.register(r"season", SeasonViewSet)
router.register(r"teacher", TeacherViewSet)

urlpatterns = [
    path("", index, name="index"),
    # path("", logout, name="logout"),
    path("api/", include(router.urls)),
]
