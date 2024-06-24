from members.models import (
    Course,
    Member,
    Season,
    Teacher,
)
from members.api.serializers import (
    CourseCopySeasonSerializer,
    CourseRetrieveSerializer,
    CourseSerializer,
    MemberRetrieveSerializer,
    MemberSerializer,
    SeasonSerializer,
    TeacherSerializer,
)

from rest_framework import status
from rest_framework.decorators import action
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

    def get_queryset(self):
        queryset = Season.objects.all()
        is_current = self.request.query_params.get("is_current", "")
        if is_current.lower() in ["true", 1]:
            queryset = queryset.filter(is_current=True)
        elif is_current.lower() in ["false", 0]:
            queryset = queryset.filter(is_current=False)
        return queryset.order_by("-year")

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
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.request.method.lower() == "get":
            return CourseRetrieveSerializer
        return CourseSerializer

    def get_queryset(self):
        queryset = Course.objects.all()
        season = self.request.query_params.get("season")
        if season:
            queryset = queryset.filter(season__id=season)
        return queryset.order_by("-season__year", "weekday", "start_hour")

    @action(methods=["post"], detail=False)
    def copy_season(self, request: Request) -> Response:
        body = CourseCopySeasonSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        Course.objects.copy_from_season(**body.validated_data)
        answer = CourseRetrieveSerializer(
            Course.objects.filter(season_id=body.validated_data["to_season"]).all(),
            many=True,
        )
        return Response(answer.data)


class MemberViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.request.method.lower() == "get":
            return MemberRetrieveSerializer
        return MemberSerializer

    def get_queryset(self):
        queryset = Member.objects.all()
        season = self.request.query_params.get("season")
        if season:
            queryset = queryset.filter(season__id=season)
        return queryset.order_by("-season__year", "last_name", "first_name")

    def create(self, request: Request, *a, **k) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer: MemberSerializer):
        user = self.get_object().user
        serializer.save(user=user)
