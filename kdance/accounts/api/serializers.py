import logging
import re

from contextlib import suppress
from datetime import timedelta
from hashlib import sha512
from secrets import token_urlsafe
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import Profile, ResetPassword
from members.models import Member, Payment, Season
from members.api.serializers import (
    MemberRetrieveSerializer,
    PaymentSerializer,
)

_logger = logging.getLogger(__name__)

PHONE_FORMAT_MSG = (
    "Ce numéro de téléphone n'est pas valide. Format attendu: 0123456789."
)


class EmailNotSentException(Exception):
    pass


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("address", "postal_code", "city", "phone")

    @staticmethod
    def validate_phone(phone: str) -> str:
        return validate_phone(phone)


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
            raise serializers.ValidationError("Cet identifiant est déjà pris.")
        return username

    @staticmethod
    def validate_first_name(name: str) -> str:
        return name.title()

    @staticmethod
    def validate_last_name(name: str) -> str:
        return name.title()

    @staticmethod
    def validate_email(email: str) -> str:
        if User.objects.filter(email=email.lower()).exists():
            raise serializers.ValidationError(
                "Un utilisateur est déjà associé à cet email."
            )
        if re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            return email.lower()
        raise serializers.ValidationError(
            "Cette adresse email ne semble pas avoir un format valide."
        )

    def create(self, validated_data: dict) -> User:
        user: User = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"].lower(),
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        return user

    @transaction.atomic
    def save(self, **kwargs: User) -> User:
        profile_data = self.validated_data.pop("profile", None)
        previous_email = ""
        previous_phone = ""
        previous_address = ""
        if self.instance and self.instance.email and self.validated_data.get("email"):  # type: ignore
            previous_email = self.instance.email  # type: ignore
        if (
            self.instance
            and self.instance.profile.phone  # type: ignore[union-attr]
            and profile_data
            and profile_data.get("phone")
        ):
            previous_phone = self.instance.profile.phone  # type: ignore
        if (
            self.instance
            and self.instance.profile.full_address  # type: ignore[union-attr]
            and profile_data
            and (
                profile_data.get("address")
                or profile_data.get("postal_code")
                or profile_data.get("city")
            )
        ):
            previous_address = self.instance.profile.full_address  # type: ignore
        user: User = super().save(**kwargs)
        if profile_data:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.address = profile_data.get("address")
            profile.postal_code = profile_data.get("postal_code")
            profile.city = profile_data.get("city")
            profile.phone = profile_data.get("phone")
            profile.save()
        for member in user.member_set.all():
            updated = False
            if previous_email and member.email == previous_email:
                member.email = self.validated_data.get("email")
                updated = True
            if previous_phone and member.phone == previous_phone:
                member.phone = profile_data.get("phone")
                updated = True
            if previous_address and member.full_address == previous_address:
                member.address = profile_data.get("address")
                member.postal_code = profile_data.get("postal_code")
                member.city = profile_data.get("city")
                updated = True
            if updated:
                _logger.debug("update")
                member.save()
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

    @staticmethod
    def validate_password(pwd: str) -> str:
        validate_pwd(pwd)
        return pwd

    @staticmethod
    def validate_phone(phone: str) -> str:
        return validate_phone(phone)

    @transaction.atomic
    def save(self, **kwargs: User) -> User:
        user: User = super().save(**kwargs)
        if Season.objects.filter(is_current=True).exists():
            payment = Payment(user=user, season=Season.objects.get(is_current=True))
            payment.save()
        return user

    @classmethod
    def send_email(cls, username: str) -> None:
        with suppress(User.DoesNotExist):
            user: User = User.objects.get(username=username)
            _logger.info("Envoi d'un email de création de compte")
            _logger.debug(f"Envoi vers {user.email}")
            mail = EmailMultiAlternatives(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL],
                subject="Création d'un compte K'Dance",
                body=cls.__build_text(username),
            )
            mail.attach_alternative(cls.__build_html(username), "text/html")
            sent = mail.send()
            if not sent:
                _logger.warning(
                    "Echec de l'envoi du mail de création de compte pour %s", username
                )

    @staticmethod
    def __build_text(username: str) -> str:
        message = f"""
Bonjour,

Vous venez de créer votre compte K'Dance! Utilisez votre email ({username}) comme identifiant pour vous connecter.
Vous pouvez désormais ajouter et gérer les adhérents de votre famille pour chaque nouvelle saison.
N'oubliez pas d'utiliser également cet espace pour mettre à jour vos coordonnées en cas de changement.

Bonne journée et à bientôt,
Tech K'Dance
"""
        return message

    @staticmethod
    def __build_html(username: str) -> str:
        message = f"""
<p>Bonjour,</p>
<p>
  Vous venez de créer votre compte K'Dance! Utilisez votre email ({username}) comme identifiant pour vous connecter.
  Vous pouvez désormais ajouter et gérer les adhérents de votre famille pour chaque nouvelle saison.
</p>
<p>
  N'oubliez pas d'utiliser également cet espace pour mettre à jour vos coordonnées en cas de changement.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        return message


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

    @classmethod
    def send_email(cls, username: str) -> None:
        with suppress(User.DoesNotExist):
            user: User = User.objects.get(username=username)
            _logger.info("Envoi d'un email de suppression de compte")
            _logger.debug(f"Envoi vers {user.email}")
            mail = EmailMultiAlternatives(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL],
                subject="Suppression de votre compte K'Dance",
                body=cls.__build_text(username),
            )
            mail.attach_alternative(cls.__build_html(username), "text/html")
            sent = mail.send()
            if not sent:
                _logger.warning(
                    "Echec de l'envoi du mail de suppression de compte pour %s",
                    username,
                )

    @staticmethod
    def __build_text(username: str) -> str:
        message = f"""
Bonjour,

Votre compte K'Dance associé à l'adresse {username} a bien été supprimé.

Bonne journée et à bientôt,
Tech K'Dance
"""
        return message

    @staticmethod
    def __build_html(username: str) -> str:
        message = f"""
<p>Bonjour,</p>
<p>
  Votre compte K'Dance associé à l'adresse {username} a bien été supprimé.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        return message


class UserAdminActionSerializer(serializers.Serializer):
    emails = serializers.ListField(child=serializers.CharField())

    def __init__(self, *, is_admin: bool, **kwargs: Any) -> None:
        self._is_admin = is_admin
        super().__init__(**kwargs)

    def validate_emails(self, emails: list[str]) -> list:
        normalized = [email.lower() for email in emails]
        if settings.SUPERUSER_EMAIL in normalized and not self._is_admin:
            raise serializers.ValidationError(
                f"{settings.SUPERUSER_EMAIL}: cet utilisateur ne peut pas être supprimé des administrateurs."
            )
        return normalized

    def save(self, **k_) -> dict:
        emails = self.validated_data.get("emails", [])
        details: dict[str, list[str]] = {
            "processed": [],
            "not_found": [],
            "other": [],
        }
        for email in emails:
            try:
                user = User.objects.get(email=email)
                user.is_superuser = self._is_admin
                user.save()
            except User.DoesNotExist:
                details["not_found"].append(email)
            except Exception:
                details["other"].append(email)
            else:
                details["processed"].append(email)
        return details


class UserTeacherActionSerializer(serializers.Serializer):
    emails = serializers.ListField(child=serializers.CharField())

    def __init__(self, *, is_teacher: bool, **kwargs: Any) -> None:
        self._is_teacher = is_teacher
        super().__init__(**kwargs)

    def validate_emails(self, emails: list[str]) -> list:
        return [email.lower() for email in emails]

    def save(self, **k_) -> dict:
        emails = self.validated_data.get("emails", [])
        details: dict[str, list[str]] = {
            "processed": [],
            "not_found": [],
            "other": [],
        }
        for email in emails:
            try:
                user = User.objects.get(email=email)
                teacher_group = Group.objects.get(name=settings.TEACHER_GROUP_NAME)
                if self._is_teacher:
                    user.groups.add(teacher_group)
                else:
                    user.groups.remove(teacher_group)
            except User.DoesNotExist:
                details["not_found"].append(email)
            except Group.DoesNotExist:
                details["other"].append("Ce groupe n'existe pas.")
            except Exception:
                _logger.exception(email)
                details["other"].append(email)
            else:
                details["processed"].append(email)
        return details


class UserChangePwdSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def __init__(self, user: User, **kwargs: Any) -> None:
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

    @staticmethod
    def validate_email(email: str) -> str:
        user = User.objects.filter(email=email.lower()).first()
        if not user:
            raise serializers.ValidationError(
                "Email incorrect, cet utilisateur n'existe pas."
            )
        return email.lower()

    def save(self, **kwargs: Any) -> None:
        user = User.objects.filter(email=self.validated_data["email"]).first()
        path = kwargs.pop("path")
        if not user or path is None:
            raise
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
        _logger.info("Envoi d'un email de réinitialisation de mot de passe")
        _logger.debug(f"Envoi vers {user.email}")
        mail = EmailMultiAlternatives(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
            subject="Réinitialisation du mot de passe K'Dance",
            body=self.__build_text(path + "pwd_new?token=" + token),
        )
        mail.attach_alternative(
            self.__build_html(path + "pwd_new?token=" + token), "text/html"
        )
        sent = mail.send()
        if not sent:
            raise EmailNotSentException(
                f"Email de ré-initialisation non envoyé à {user.email}"
            )

    @classmethod
    def __build_text(cls, url: str) -> str:
        message = f"""
Bonjour,

Vous venez de faire une demande de réinitialisation de mot de passe pour votre compte K'Dance ?
Veuillez cliquer sur le lien suivant, ou le copier-coller dans votre navigateur: {url}
Ce lien restera valide 30 minutes.

Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email, votre mot de passe restera inchangé.

Bonne journée et à bientôt,
Tech K'Dance
"""
        return message

    @classmethod
    def __build_html(cls, url: str) -> str:
        message = f"""
<p>Bonjour,</p>
<p>
  Vous venez de faire une demande de réinitialisation de mot de passe pour votre compte K'Dance ?
  Veuillez cliquer sur le lien suivant, qui restera valide pendant 30 minutes:
  <a href="{url}">
    {url}
  </a>
</p>
<p>Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email, votre mot de passe restera
  inchangé.</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        return message


class UserNewPwdSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
    token = serializers.CharField()

    @staticmethod
    def validate_password(pwd: str) -> str:
        validate_pwd(pwd)
        return pwd

    @staticmethod
    def validate_email(email: str) -> str:
        return email.lower()

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        user = User.objects.filter(email=validated.get("email")).first()
        if not user:
            raise serializers.ValidationError(
                {"email": ["Email incorrect, cet utilisateur n'existe pas."]}
            )
        reset_pwd = ResetPassword.objects.filter(user=user).first()
        if not reset_pwd:
            raise serializers.ValidationError(
                {
                    "email": [
                        "Email incorrect, aucune demande de réinitialisation trouvée."
                    ]
                }
            )
        if (
            reset_pwd.request_hash
            != sha512(validated.get("token").encode()).hexdigest()
        ):
            raise serializers.ValidationError(
                {"token": ["Lien de réinitialisation incorrect pour cet utilisateur."]}
            )
        if timezone.now() - reset_pwd.created > timedelta(minutes=31):
            raise serializers.ValidationError(
                {
                    "token": [
                        "Lien de réinitialisation expiré. Veuillez refaire une demande de réinitialisation."
                    ]
                }
            )
        return validated

    @transaction.atomic
    def save(self, **k_) -> None:
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["password"])
        user.save()
        ResetPassword.objects.filter(user=user).delete()


def validate_pwd(pwd: str) -> None:
    if not pwd or len(pwd) < 12:
        raise serializers.ValidationError(
            "Votre mot de passe doit contenir au moins 12 caractères."
        )
    if all(letter.isupper() for letter in pwd if letter.isalpha()):
        raise serializers.ValidationError(
            "Votre mot de passe doit contenir au moins une minuscule."
        )
    if all(letter.islower() for letter in pwd if letter.isalpha()):
        raise serializers.ValidationError(
            "Votre mot de passe doit contenir au moins une majuscule."
        )
    if not any(letter.isdigit() for letter in pwd):
        raise serializers.ValidationError(
            "Votre mot de passe doit contenir au moins un chiffre."
        )


def validate_phone(phone: str) -> str:
    if re.fullmatch(r"\d{10}", phone):
        return phone
    raise serializers.ValidationError(
        "Ce numéro de téléphone n'est pas valide. Format attendu: 0123456789."
    )
