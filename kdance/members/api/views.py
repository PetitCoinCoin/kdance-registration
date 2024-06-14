from members.models import (
    Course,
    Member,
    Season,
    Teacher,
)
from members.api.serializers import (
    CourseSerializer,
    MemberSerializer,
    SeasonSerializer,
    TeacherSerializer,
)

from rest_framework import status
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet


class SeasonViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    queryset = Season.objects.all().order_by("-year")
    serializer_class = SeasonSerializer
    http_method_names = ["get", "post", "patch", "delete"]


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
    http_method_names = ["get", "post", "patch", "delete"]


class CourseViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = CourseSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        queryset = Course.objects.all()
        season = self.request.query_params.get("season")
        if season:
            queryset = queryset.filter(season__year=season)
        return queryset.order_by("-season__year", "weekday")


class MemberViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    queryset = Member.objects.all().order_by("-pk")
    serializer_class = MemberSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def create(self, request: Request, *a, **k) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)