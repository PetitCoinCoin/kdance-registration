import logging

from enum import Enum
from typing import Any

from django.contrib.auth.models import User
from django.db import transaction
from django.db.utils import IntegrityError
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from members.models import (
    Ancv,
    Check,
    Contact,
    Course,
    Documents,
    Member,
    OtherPayment,
    Payment,
    Season,
    SportCoupon,
    SportPass,
    Teacher,
)

_logger = logging.getLogger(__name__)


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = (
            "id",
            "year",
            "is_current",
            "discount_percent",
            "discount_limit",
        )

    @staticmethod
    def validate_year(year: str) -> str:
        last_season = Season.objects.order_by("year").last()
        if last_season and year < last_season.year:
            raise serializers.ValidationError(
                "On ne peut pas créer de saison dans le passé !"
            )
        return year


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ("id", "name")

    def validate_name(self, name: str) -> str:
        if Teacher.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError("Ce professeur existe déjà.")
        return name


class CourseSerializer(serializers.ModelSerializer):
    weekday = serializers.ChoiceField(
        choices=[
            (0, "Lundi"),
            (1, "Mardi"),
            (2, "Mercredi"),
            (3, "Jeudi"),
            (4, "Vendredi"),
            (5, "Samedi"),
            (6, "Dimanche"),
        ],
    )

    class Meta:
        model = Course
        fields = (
            "id",
            "name",
            "teacher",
            "season",
            "price",
            "weekday",
            "start_hour",
            "end_hour",
        )


class CourseRetrieveSerializer(CourseSerializer):
    teacher = TeacherSerializer()
    season = SeasonSerializer()


class CourseCopySeasonSerializer(serializers.Serializer):
    from_season = serializers.IntegerField(required=True)
    to_season = serializers.IntegerField(required=True)

    @staticmethod
    def validate_from_season(season_id: int) -> int:
        if not Season.objects.filter(id=season_id).exists():
            raise serializers.ValidationError("Cette saison n'existe pas.")
        return season_id

    @staticmethod
    def validate_to_season(season_id: int) -> int:
        if not Season.objects.filter(id=season_id).exists():
            raise serializers.ValidationError("Cette saison n'existe pas.")
        return season_id


class DocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documents
        fields = (
            "authorise_photos",
            "authorise_emergency",
            "medical_document",
        )


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "contact_type",
        )
        extra_kwargs = {
            "email": {"required": False},
        }

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        if (
            not validated.get("email", "")
            and validated.get("contact_type") == Contact.ContactEnum.RESPONSIBLE.value
        ):
            raise serializers.ValidationError(
                {"email": ["L'email est obligatoire pour le responsable."]}
            )
        return validated


class AncvSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ancv
        fields = ("amount", "count")

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        if validated.get("amount", 0) > 0 and validated.get("count", 0) == 0:
            raise serializers.ValidationError(
                {"count": ["Une valeur non nulle est obligatoire."]}
            )
        if validated.get("count", 0) > 0 and validated.get("amount", 0) == 0:
            raise serializers.ValidationError(
                {"amount": ["Une valeur non nulle est obligatoire."]}
            )
        return validated


class SportCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportCoupon
        fields = ("amount", "count")

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        if validated.get("amount", 0) > 0 and validated.get("count", 0) == 0:
            raise serializers.ValidationError(
                {"count": ["Une valeur non nulle est obligatoire."]}
            )
        if validated.get("count", 0) > 0 and validated.get("amount", 0) == 0:
            raise serializers.ValidationError(
                {"amount": ["Une valeur non nulle est obligatoire."]}
            )
        return validated


class OtherPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherPayment
        fields = ("amount", "comment")


class CheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Check
        fields = (
            "amount",
            "bank",
            "month",
            "name",
            "number",
            "payment",
        )


class PaymentSerializer(WritableNestedModelSerializer, serializers.ModelSerializer):
    season = SeasonSerializer()
    ancv = AncvSerializer(required=False)
    sport_coupon = SportCouponSerializer(required=False)
    other_payment = OtherPaymentSerializer(required=False)
    check_payment = CheckSerializer(many=True)
    user_email = serializers.CharField(
        read_only=True,
        source="user.username",
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "season",
            "paid",
            "due",
            "due_detail",
            "cash",
            "sport_coupon",
            "ancv",
            "check_payment",
            "other_payment",
            "comment",
            "refund",
            "special_discount",
            "user_email",
            "sport_pass_count",
            "sport_pass_amount",
        )

    def validate(self, attr: dict) -> dict:
        if not attr.get("other_payment", {}).get("comment", "") and not attr.get(
            "other_payment", {}
        ).get("amount", 0):
            attr.pop("other_payment", None)
        return super().validate(attr)

    @transaction.atomic
    def save(self, **kwargs: Payment):
        checks_data = self.validated_data.pop("check_payment", [])
        payment = super().save(**kwargs)
        if checks_data:
            for check in payment.check_payment.all():
                check.delete()
        for check_payment in checks_data:
            Check(payment=payment, **check_payment).save()


class SportPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportPass
        fields = ("amount", "code")


class MemberSerializer(WritableNestedModelSerializer, serializers.ModelSerializer):
    documents = DocumentsSerializer()
    payment = PaymentSerializer(required=False, read_only=True)
    sport_pass = SportPassSerializer(required=False)
    contacts = ContactSerializer(many=True)
    active_courses = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Course.objects.all(),
        default=list,
    )
    cancelled_courses = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Course.objects.all(),
        default=list,
    )

    class Meta:
        model = Member
        fields = (
            "id",
            "created",
            "first_name",
            "last_name",
            "birthday",
            "address",
            "email",
            "phone",
            "season",
            "active_courses",
            "cancelled_courses",
            "ffd_license",
            "is_validated",
            "documents",
            "contacts",
            "payment",
            "sport_pass",
            "cancel_refund",
        )
        extra_kwargs = {"created": {"read_only": True}}

    def validate_active_courses(self, courses: list) -> list:
        if not len(courses):
            raise serializers.ValidationError(
                "Vous devez sélectionner au moins un cours."
            )
        return courses

    @transaction.atomic
    def save(self, **kwargs: Member) -> None:
        username = kwargs.get("user")
        self.validated_data["user"] = User.objects.get(username=username)
        contacts = self.validated_data.pop("contacts", None)
        documents = self.validated_data.pop("documents", None) if self.partial else None
        try:
            member = super().save()
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "first_name": ["Cet adhérent existe déjà pour la saison."],
                    "last_name": ["Cet adhérent existe déjà pour la saison."],
                }
            )
        if contacts is not None:
            member.contacts.clear()
            for contact in contacts:
                contact_instance, _ = Contact.objects.get_or_create(**contact)
                member.contacts.add(contact_instance)
            Contact.objects.clean_orphan()
        if documents is not None:
            doc = Documents.objects.get(member=member)
            for key, value in documents.items():
                setattr(doc, key, value)
            doc.save()


class MemberRetrieveSerializer(MemberSerializer):
    active_courses = CourseRetrieveSerializer(many=True)  # type:ignore[assignment]
    cancelled_courses = CourseRetrieveSerializer(many=True)  # type:ignore[assignment]
    season = SeasonSerializer()


class MemberCoursesActionsEnum(Enum):
    ADD = "add"
    REMOVE = "remove"


class MemberCoursesSerializer(serializers.Serializer):
    courses = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Course.objects.all(),
        default=list,
    )
    cancel_refund = serializers.FloatField(required=False)

    def __init__(self, member: Member, action: str, **kwargs: Any) -> None:
        self._member = member
        self._action = MemberCoursesActionsEnum(action)
        super().__init__(**kwargs)

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        if (
            self._action == MemberCoursesActionsEnum.REMOVE
            and validated.get("cancel_refund") is None
        ):
            raise serializers.ValidationError(
                {"cancel_refund": ["Ce champ est obligatoire pour retirer un cours."]}
            )
        if (
            self._action == MemberCoursesActionsEnum.ADD
            and validated.get("cancel_refund") is not None
        ):
            raise serializers.ValidationError(
                {
                    "cancel_refund": [
                        "Ce champ ne doit pas être modifié pour ajouter un cours."
                    ]
                }
            )
        return validated

    def save(self, **kwargs: Any) -> None:
        if self._action == MemberCoursesActionsEnum.ADD:
            self._member.active_courses.add(*self.validated_data.get("courses", []))
            self._member.cancelled_courses.remove(
                *self.validated_data.get("courses", [])
            )
            self._member.save()
        elif self._action == MemberCoursesActionsEnum.REMOVE:
            self._member.cancelled_courses.add(*self.validated_data.get("courses", []))
            self._member.active_courses.remove(*self.validated_data.get("courses", []))
            self._member.cancel_refund = self.validated_data.get("cancel_refund")
            self._member.save()
