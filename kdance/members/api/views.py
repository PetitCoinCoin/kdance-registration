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

    def create(self, request: Request, *a, **k) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)