from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as UserType
from django.db import transaction
from rest_framework import serializers

from accounts.models import Profile
from members.models import Payment, Season
from members.api.serializers import PaymentSerializer

User = get_user_model()


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField(
        read_only=True,
        required=False,
        default="",
        allow_blank=True,
    )


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("address", "phone")


class UserBaseSerializer(serializers.ModelSerializer):
    def create(self, validated_data: dict) -> UserType:
        user: UserType = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        return user

    @classmethod
    @transaction.atomic
    def delete(cls, user: UserType) -> None:
        if user.is_superuser:
            raise serializers.ValidationError("Cet utilisateur ne peut pas être supprimé.")
        user.delete()

    @transaction.atomic
    def save(self, **kwargs: UserType) -> None:
        profile_data = self.validated_data.pop("profile")
        user: UserType = super().save(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.address = profile_data.get("address")
        profile.phone = profile_data.get("phone")
        profile.save()


class UserCreateSerializer(UserBaseSerializer):
    address = serializers.CharField(
        required=True,
        allow_blank=False,
        source="profile.address",
    )
    phone = serializers.CharField(
        required=True,
        allow_blank=False,
        source="profile.phone",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "address",
            "phone",
        )
        extra_kwargs = {
            "username": {"required": True},
            "password": {"write_only": True, "required": True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    @classmethod
    def validate_password(cls, pwd: str) -> str:
        validate_pwd(pwd)
        return pwd

    @classmethod
    def validate_email(cls, email: str) -> str:
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Un utilisateur est déjà associé à cet email.")
        return email

    @transaction.atomic
    def save(self, **kwargs: UserType) -> None:
        user: UserType = super().save(**kwargs)
        payment = Payment(user=user, season=Season.objects.get(is_current=True))
        payment.save()

class UserSerializer(UserBaseSerializer):
    profile = ProfileSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "profile",
            "payment",
        )
        read_only_fields = fields

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            try:
                users = iter(args[0])
            except TypeError:
                users = [args[0]]
            for user in users:
                user.profile = Profile.objects.get(user=user)
                user.payment = Payment.objects.get(user=user)
        super().__init__(*args, **kwargs)


class UserChangePwdSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def __init__(self, user: UserType, **kwargs: Any) -> None:
        self._user = user
        super().__init__(**kwargs)

    def validate_old_password(self, pwd: str) -> str:
        if not self._user.check_password(pwd):
            raise serializers.ValidationError("Mot de passe actuel invalide.")
        return pwd

    def validate_new_password(self, pwd: str) -> str:
        validate_pwd(pwd)
        return pwd

    def save(self, **k_) -> None:
        self._user.set_password(self.validated_data["new_password"])
        self._user.save()


def validate_pwd(pwd: str) -> None:
    if not pwd or len(pwd) < 8:
            raise serializers.ValidationError("Votre mot de passe doit contenir au moins 8 caractères.")
    if all(letter.islower() for letter in pwd):
        raise serializers.ValidationError("Votre mot de passe doit contenir au moins une majuscule.")
    if all(letter.isupper() for letter in pwd):
        raise serializers.ValidationError("Votre mot de passe doit contenir au moins une minuscule.")
    if not any(letter.isdigit() for letter in pwd):
        raise serializers.ValidationError("Votre mot de passe doit contenir au moins un chiffre.")
    if pwd.replace(" ", "").isalnum():
        raise serializers.ValidationError("Votre mot de passe doit contenir au moins un caractère spécial.")
