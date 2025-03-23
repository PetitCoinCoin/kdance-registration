from members.models import (
    Check,
    Course,
    GeneralSettings,
    Member,
    Payment,
    Season,
    Teacher,
)
from members.api.serializers import (
    CheckSerializer,
    CourseCopySeasonSerializer,
    CourseRetrieveSerializer,
    CourseSerializer,
    GeneralSettingsSerializer,
    MemberCoursesActionsEnum,
    MemberCoursesSerializer,
    MemberRetrieveSerializer,
    MemberRetrieveShortSerializer,
    MemberSerializer,
    PaymentSerializer,
    SeasonSerializer,
    TeacherSerializer,
)

from django.conf import settings
from django.db.models import Q
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
from rest_framework import serializers
from rest_framework.viewsets import GenericViewSet


class GeneralSettingsViewSet(
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    queryset = GeneralSettings.objects.all()
    serializer_class = GeneralSettingsSerializer
    http_method_names = ["get", "put"]

    def get_object(self) -> GeneralSettings:
        return GeneralSettings.get_solo()


class SeasonViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    queryset = Season.objects.all().order_by("-year")
    serializer_class = SeasonSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        queryset = Season.objects.all()
        is_current = self.request.query_params.get("is_current", "")
        if is_current.lower() in ["true", "1"]:
            queryset = queryset.filter(is_current=True)
        elif is_current.lower() in ["false", "0"]:
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
    queryset = Teacher.objects.all().order_by("name")
    serializer_class = TeacherSerializer
    http_method_names = ["get", "post", "patch", "delete"]


class PaymentViewSet(
    ListModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = PaymentSerializer
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        queryset = Payment.objects.all()
        season = self.request.query_params.get("season")
        if season:
            queryset = queryset.filter(season__id=season)
        return queryset.order_by("-season__year", "user__username")


class CheckViewSet(
    ListModelMixin,
    GenericViewSet,
):
    serializer_class = CheckSerializer
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = Check.objects.all()
        season = self.request.query_params.get("season")
        month = self.request.query_params.get("month")
        if season:
            queryset = queryset.filter(payment__season__id=season)
        if month:
            queryset = queryset.filter(month=month)
        return queryset.order_by("-payment__season__year", "month", "bank")


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
        return queryset.order_by("-season__year", "teacher__name", "name")

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
    http_method_names = ["get", "post", "patch", "delete", "put"]

    def get_serializer_class(self):
        if self.request.method.lower() == "get":
            if self.request.query_params.get("without_details", "").lower() in [
                "true",
                "1",
            ]:
                return MemberRetrieveShortSerializer
            return MemberRetrieveSerializer
        return MemberSerializer

    def get_queryset(self):
        queryset = Member.objects.all()
        season = self.request.query_params.get("season")
        course = self.request.query_params.get("course")
        with_pass = self.request.query_params.get("with_pass")
        with_license = self.request.query_params.get("with_license")
        if season:
            queryset = queryset.filter(season__id=season)
        if course:
            queryset = queryset.filter(
                Q(active_courses__id=course) | Q(cancelled_courses__id=course)
            )
        if with_pass:
            queryset = queryset.filter(
                sport_pass__isnull=with_pass.lower() not in ["true", "1", "y"]
            )
        if with_license:
            if with_license.lower() in ["true", "1", "y"]:
                queryset = queryset.filter(ffd_license__gt=0)
            else:
                queryset = queryset.filter(ffd_license=0)
        return (
            queryset.select_related("documents", "season", "user")
            .prefetch_related("active_courses", "cancelled_courses")
            .order_by("-season__year", "last_name", "first_name")
        )

    def retrieve(self, request: Request, *a, **k) -> Response:
        instance = self.get_object()
        if not request.user.is_superuser and instance.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request: Request, *a, **k) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        if (
            not request.user.is_superuser
            and not request.user.groups.filter(
                name=settings.TEACHER_GROUP_NAME
            ).exists()
        ):
            queryset = queryset.filter(user__id=request.user.pk)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request: Request, *a, **k) -> Response:
        if not GeneralSettings.get_solo().allow_new_member:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        headers = self.get_success_headers(serializer.data)
        serializer.send_email(self.request.user.username)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        if request.method and request.method.lower() == "put":
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        instance = self.get_object()
        if not request.user.is_superuser and instance.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer: serializers.BaseSerializer):
        user = self.get_object().user
        serializer.save(user=user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_superuser and instance.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["put"],
        serializer_class=MemberCoursesSerializer,
        url_path=r"courses/(?P<action>\w+)",
    )
    def courses(self, request: Request, action: str, *_a, **_k) -> Response:
        if action not in [action.value for action in MemberCoursesActionsEnum]:
            return Response(status=status.HTTP_404_NOT_FOUND)
        member = self.get_object()
        serializer = MemberCoursesSerializer(
            data=request.data, member=member, action=action
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
