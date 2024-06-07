from members.models import (
    Course,
    Season,
    Teacher,
)
from members.api.serializers import (
    CourseSerializer,
    SeasonSerializer,
    TeacherSerializer,
)

from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.viewsets import GenericViewSet


class SeasonViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    queryset = Season.objects.all().order_by("-pk")
    serializer_class = SeasonSerializer


class TeacherViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    queryset = Teacher.objects.all().order_by("pk")
    serializer_class = TeacherSerializer


class CourseViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    queryset = Course.objects.all().order_by("-pk")
    serializer_class = CourseSerializer
