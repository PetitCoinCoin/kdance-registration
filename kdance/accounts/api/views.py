from django.conf import settings
from django.contrib.auth import (
    authenticate,
    login,
    update_session_auth_hash,
)
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from accounts.api.serializers import (
    UserAdminActionSerializer,
    UserBaseSerializer,
    UserChangePwdSerializer,
    UserCreateSerializer,
    UserNewPwdSerializer,
    UserResetPwdSerializer,
    UserSerializer,
    UserTeacherActionSerializer,
)
from members.models import GeneralSettings


class UsersApiViewSet(
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    def get_queryset(self):
        queryset = User.objects.prefetch_related("profile").all()
        admin = self.request.query_params.get("admin")
        teacher = self.request.query_params.get("teacher")
        if admin:
            queryset = queryset.filter(
                is_superuser=(admin.lower() in ["true", "1", "y"])
            )
        if teacher and teacher.lower() in ["true", "1", "y"]:
            queryset = queryset.filter(groups__name=settings.TEACHER_GROUP_NAME)
        return queryset.order_by("last_name")

    def get_serializer_class(
        self,
    ) -> type[
        UserBaseSerializer | UserAdminActionSerializer | UserTeacherActionSerializer
    ]:
        if self.request.method and self.request.method.lower() == "post":
            return UserCreateSerializer
        if self.request.method and self.request.method.lower() == "put":
            if self.request.path and "admin" in self.request.path.lower():
                return UserAdminActionSerializer
            return UserTeacherActionSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs) -> Response:
        if not GeneralSettings.get_solo().allow_signup:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        response = super().create(request, *args, **kwargs)
        username = request.data.get("username")
        password = request.data.get("password")
        if not request.user.is_authenticated:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
        UserCreateSerializer.send_email(username)
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.username == settings.SUPERUSER_EMAIL:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        self.perform_destroy(instance)
        UserSerializer.send_email(self.request.user.username)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["put"])
    def admin(self, request: Request, action: str) -> Response:
        if action not in ("activate", "deactivate"):
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(
            data=request.data, is_admin=action == "activate"
        )
        serializer.is_valid(raise_exception=True)
        details = serializer.save()
        if not details["processed"]:
            # only emails not found
            if not details["other"]:
                return Response(status=status.HTTP_400_BAD_REQUEST, data=details)
            else:
                return Response(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=details
                )
        return Response(data=details)

    @action(detail=False, methods=["put"])
    def teacher(self, request: Request, action: str) -> Response:
        if action not in ("activate", "deactivate"):
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(
            data=request.data, is_teacher=action == "activate"
        )
        serializer.is_valid(raise_exception=True)
        details = serializer.save()
        if not details["processed"]:
            # only emails not found
            if not details["other"]:
                return Response(status=status.HTTP_400_BAD_REQUEST, data=details)
            else:
                return Response(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=details
                )
        return Response(data=details)


class UserMeApiViewSet(
    DestroyModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "put", "delete"]

    def get_object(self) -> User:
        return self.queryset.get(pk=self.request.user.pk)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.username == settings.SUPERUSER_EMAIL:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if request.data.get("username", "").lower() == instance.username.lower():
            request.data.pop("username")
        if request.data.get("email", "").lower() == instance.email.lower():
            request.data.pop("email")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=["put"])
    def password(self, request: Request) -> Response:
        user = self.get_object()
        serializer = UserChangePwdSerializer(user=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["put"])
    def validate(self, request: Request) -> Response:
        user = self.get_object()
        for member in user.member_set.filter(season__is_current=True).all():
            member.is_validated = True
            member.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordApiViewSet(GenericViewSet):
    http_method_names = ["post"]

    def get_serializer_class(
        self,
    ) -> type[UserResetPwdSerializer | UserNewPwdSerializer]:
        if self.request.path and "reset" in self.request.path.lower():
            return UserResetPwdSerializer
        return UserNewPwdSerializer

    @action(detail=False, methods=["post"])
    def reset(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(path=request.build_absolute_uri("/"))
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["post"])
    def new(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = User.objects.get(email=serializer.validated_data.get("email"))
        update_session_auth_hash(request, user)
        auth_user = authenticate(
            username=user.username, password=request.data.get("password")
        )
        if auth_user is not None:
            login(request, user)
        return Response(status=status.HTTP_200_OK)
