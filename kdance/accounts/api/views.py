from django.contrib.auth import (
    get_user_model,
    update_session_auth_hash,
)
from django.contrib.auth.models import User as UserType
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
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from accounts.api.serializers import (
    UserAdminActionSerializer,
    UserChangePwdSerializer,
    UserCreateSerializer,
    UserNewPwdSerializer,
    UserResetPwdSerializer,
    UserSerializer,
)

User = get_user_model()


class UsersApiViewSet(
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    def get_queryset(self):
        queryset = User.objects.prefetch_related("profile").all()
        admin = self.request.query_params.get("admin")
        if admin:
            queryset = queryset.filter(
                is_superuser=(admin.lower() in ["true", "1", "y"])
            )
        return queryset.order_by("last_name")

    def get_serializer_class(self) -> Serializer:
        if self.request.method and self.request.method.lower() == "post":
            return UserCreateSerializer
        if self.request.method and self.request.method.lower() == "put":
            return UserAdminActionSerializer
        return UserSerializer

    @action(detail=False, methods=["put"])
    def admin(self, request: Request, action: str) -> Response:
        if action not in ("activate", "deactivate"):
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data, is_admin=action == "activate")
        serializer.is_valid(raise_exception=True)
        details = serializer.save()
        if not details["processed"]:
            # only emails not found
            if not details["other"]:
                return Response(status=status.HTTP_400_BAD_REQUEST, data=details)
            else:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=details)
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

    def get_object(self) -> UserType:
        return self.queryset.get(pk=self.request.user.pk)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if request.data.get("username").lower() == instance.username.lower():
            request.data.pop("username")
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


class PasswordApiViewSet(GenericViewSet):
    http_method_names = ["post"]

    def get_serializer_class(self) -> Serializer:
        if self.request.path and "reset" in self.request.path.lower():
            return UserResetPwdSerializer
        return UserNewPwdSerializer

    @action(detail=False, methods=["post"])
    def reset(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data.get("email")).first()
        if not user:
            return Response(
                data={"email": ["Cet email n'est associé à aucun utilisateur."]},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer.save(user=user, path=request.build_absolute_uri("/"))
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["post"])
    def new(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)
