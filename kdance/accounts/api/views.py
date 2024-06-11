from cryptography.fernet import Fernet
from django.contrib.auth import (
    get_user_model,
    update_session_auth_hash,
)
from django.contrib.auth.models import User as UserType
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer, ValidationError
from rest_framework.viewsets import GenericViewSet

from accounts.api.serializers import (
    DetailSerializer,
    UserChangePwdSerializer,
    UserCreateSerializer,
    UserSerializer,
    validate_pwd,
)

User = get_user_model()


class UsersApiViewSet(
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    queryset = User.objects.prefetch_related("profile").all().order_by("last_name")

    def get_serializer_class(self) -> Serializer:
        if self.request.method and self.request.method.lower() == "post":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=["put"])
    def password(self, _r: Request) -> Response:
        user = self.get_object()
        i = 0
        try_max = 100
        while i < try_max:
            pwd = "".join(Fernet.generate_key().decode("utf-8") for _ in range(3))[:12]
            try:
                validate_pwd(pwd)
            except ValidationError:
                i += 1
            else:
                break
        if i == try_max:
            raise APIException("Impossible de regénérer un mot de passe. Merci de réessayer")
        user.set_password(pwd)
        user.save()
        answer = DetailSerializer(data={"detail": pwd})
        answer.is_valid(raise_exception=True)
        return Response(answer)


class UserMeApiViewSet(
    DestroyModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self) -> UserType:
        return self.queryset.get(pk=self.request.user.pk)

    @action(detail=False, methods=["put"])
    def password(self, request: Request) -> Response:
        user = self.get_object()
        serializer = UserChangePwdSerializer(user=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)
