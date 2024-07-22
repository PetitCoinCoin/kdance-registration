from datetime import timedelta
from hashlib import sha512
from secrets import token_urlsafe
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as UserType
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import Profile, ResetPassword
from members.models import Member, Payment, Season
from members.api.serializers import (
    MemberRetrieveSerializer,
    PaymentSerializer,
)

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("address", "phone")


class UserBaseSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        allow_blank=False,
    )
    email = serializers.CharField(
        required=True,
        allow_blank=False,
    )
    first_name = serializers.CharField(
        required=True,
        allow_blank=False,
    )
    last_name = serializers.CharField(
        required=True,
        allow_blank=False,
    )
    date_joined = serializers.DateTimeField(format="%d/%m/%Y")
    last_login = serializers.DateTimeField(format="%d/%m/%Y")

    @staticmethod
    def validate_username(username: str) -> str:
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

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
        if user.username == settings.SUPERUSER:
            raise serializers.ValidationError("Cet utilisateur ne peut pas être supprimé.")
        user.delete()

    @transaction.atomic
    def save(self, **kwargs: UserType) -> UserType:
        profile_data = self.validated_data.pop("profile", None)
        user: UserType = super().save(**kwargs)
        if profile_data:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.address = profile_data.get("address")
            profile.phone = profile_data.get("phone")
            profile.save()
        return user


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
        if Season.objects.filter(is_current=True).exists():
            payment = Payment(user=user, season=Season.objects.get(is_current=True))
            payment.save()


class UserSerializer(UserBaseSerializer):
    profile = ProfileSerializer()
    payment = PaymentSerializer(read_only=True, many=True)
    members = MemberRetrieveSerializer(read_only=True, many=True)

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
            "members",
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
                user.payment = Payment.objects.filter(user=user).all()
                user.members = Member.objects.filter(user=user).all()
        super().__init__(*args, **kwargs)


class UserAdminActionSerializer(serializers.Serializer):
    emails = serializers.ListField(child=serializers.CharField())

    def save(self, *, is_admin: bool, **k_) -> dict:
        emails = self.validated_data.get("emails", [])
        details = {
            "processed": [],
            "not_found": [],
            "other": [],
        }
        for email in emails:
            try:
                user = User.objects.get(email=email)
                user.is_superuser = is_admin
                user.save()
            except User.DoesNotExist:
                details["not_found"].append(email)
            except:
                details["other"].append(email)
            else:
                details["processed"].append(email)
        return details


class UserChangePwdSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

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


class UserResetPwdSerializer(serializers.Serializer):
    email = serializers.CharField()

    def save(self, user: UserType, path: str, **k_) -> None:
        token = token_urlsafe()
        if not ResetPassword.objects.filter(user=user).exists():
            ResetPassword(
                user=user,
                request_hash=sha512(token.encode()).hexdigest(),
            ).save()
        else:
            reset_pwd = ResetPassword.objects.get(user=user)
            reset_pwd.request_hash = sha512(token.encode()).hexdigest()
            reset_pwd.save()
        # Send email
        print("mail envoyé (ou pas) avec cette url dedans:", path + "pwd_new?token=" + token)


class UserNewPwdSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
    token = serializers.CharField()

    @staticmethod
    def validate_password(pwd: str) -> str:
        validate_pwd(pwd)
        return pwd

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        user = User.objects.filter(email=validated.get("email")).first()
        if not user:
            raise serializers.ValidationError({"email": "Email incorrect, cet utilisateur n'existe pas."})
        reset_pwd = ResetPassword.objects.filter(user=user).first()
        if not reset_pwd:
            raise serializers.ValidationError({"email": "Email incorrect, aucune demande de réinitialisation trouvée."})
        if reset_pwd.request_hash != sha512(validated.get("token").encode()).hexdigest():
            raise serializers.ValidationError({"token": "Lien de réinitialisation incorrect pour cet utilisateur."})
        if timezone.now() - reset_pwd.created > timedelta(minutes=30):
            raise serializers.ValidationError({"token": "Lien de réinitialisation expiré. Veuillez refaire une demande de réinitialisation."})
        return validated

    @transaction.atomic
    def save(self, **k_) -> None:
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["password"])
        user.save()
        ResetPassword.objects.filter(user=user).delete()


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
