import logging

from enum import Enum
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.utils import IntegrityError
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from members.emails import EmailEnum, EmailSender
from members.models import (
    Ancv,
    Check,
    Contact,
    Course,
    Documents,
    GeneralSettings,
    Member,
    OtherPayment,
    Payment,
    Season,
    SportCoupon,
    SportPass,
    CBPayment,
    Teacher,
)

_logger = logging.getLogger(__name__)


class GeneralSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralSettings
        fields = (
            "allow_signup",
            "allow_new_member",
            "pre_signup_payment_delta_days",
            "signup_payment_delta_days",
        )


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = (
            "id",
            "year",
            "is_current",
            "pre_signup_start",
            "pre_signup_end",
            "signup_start",
            "signup_end",
            "discount_percent",
            "discount_limit",
            "pass_sport_amount",
            "ffd_a_amount",
            "ffd_b_amount",
            "ffd_c_amount",
            "ffd_d_amount",
        )

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        if (
            validated.get("pre_signup_end")
            and validated.get("pre_signup_end")
            and validated.get("pre_signup_end") < validated.get("pre_signup_start")
        ):
            raise serializers.ValidationError(
                {
                    "pre_signup_end": [
                        "La fin des pré-inscriptions ne peut être qu'après le début des pré-inscriptions."
                    ]
                }
            )

        if (
            validated.get("signup_start")
            and validated.get("pre_signup_end")
            and validated.get("signup_start") < validated.get("pre_signup_end")
        ):
            raise serializers.ValidationError(
                {
                    "signup_start": [
                        "Le début des inscriptions ne peut être qu'après la fin des pré-inscriptions."
                    ]
                }
            )
        if (
            validated.get("signup_end")
            and validated.get("signup_end")
            and validated.get("signup_end") < validated.get("signup_start")
        ):
            raise serializers.ValidationError(
                {
                    "signup_end": [
                        "La fin des inscriptions ne peut être qu'après le début des inscriptions."
                    ]
                }
            )
        return validated


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
            "capacity",
            "is_complete",
            "waiting",
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


class CBPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CBPayment
        fields = ("amount", "transaction_type")


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
    cb_payment = CBPaymentSerializer(required=False, read_only=True)
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
            "cb_payment",
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


class PaymentShortSerializer(PaymentSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "paid",
            "due",
            "refund",
            "comment",
        )


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
    )
    cancelled_courses = serializers.PrimaryKeyRelatedField(  # type: ignore
        many=True,
        read_only=True,
    )
    waiting_courses = serializers.PrimaryKeyRelatedField(  # type: ignore
        many=True,
        read_only=True,
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
            "postal_code",
            "city",
            "email",
            "phone",
            "season",
            "active_courses",
            "cancelled_courses",
            "waiting_courses",
            "ffd_license",
            "is_validated",
            "documents",
            "contacts",
            "payment",
            "sport_pass",
            "cancel_refund",
        )
        extra_kwargs = {"created": {"read_only": True}}

    @staticmethod
    def validate_active_courses(courses: list) -> list:
        if not len(courses):
            raise serializers.ValidationError(
                "Vous devez sélectionner au moins un cours."
            )
        return courses

    @staticmethod
    def validate_contacts(value: list) -> list:
        if not len(
            [contact for contact in value if contact["contact_type"] == "emergency"]
        ):
            raise serializers.ValidationError(
                "Vous devez indiquer au moins un contact d'urgence."
            )
        return value

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        if validated.get("city"):
            validated["city"] = validated["city"].title()
        if validated.get("active_courses") is not None:
            validated["waiting_courses"] = [
                course
                for course in validated.get("active_courses", [])
                if course.is_complete
            ]
            validated["active_courses"] = [
                course
                for course in validated.get("active_courses", [])
                if not course.is_complete
            ]
        return validated

    def check_presignup(self, username: str) -> None:
        if not Member.objects.filter(
            first_name=self.validated_data["first_name"],
            last_name=self.validated_data["last_name"],
            birthday=self.validated_data["birthday"],
            season__year=self.validated_data["season"].previous_season,
        ).exists():
            email_sender = EmailSender(EmailEnum.PRE_SIGNUP_WARNING)
            email_sender.send_email(
                emails=[settings.DEFAULT_FROM_EMAIL, settings.SUPERUSER_EMAIL],
                username=username,
                full_name=f"{self.validated_data['first_name']} {self.validated_data['last_name']}",
                birthday=self.validated_data["birthday"].strftime("%d/%m/%Y"),
            )

    @transaction.atomic
    def save(self, **kwargs: Any) -> Member:
        username = kwargs.get("user")
        self.validated_data["user"] = User.objects.get(username=username)
        contacts = self.validated_data.pop("contacts", None)
        documents = self.validated_data.pop("documents", None) if self.partial else None
        sport_pass = self.validated_data.pop("sport_pass", {})
        active_courses = self.validated_data.pop("active_courses", None)
        waiting_courses = self.validated_data.pop("waiting_courses", None)
        cancelled_courses = self.validated_data.pop("cancelled_courses", None)
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
        if sport_pass:
            if SportPass.objects.filter(member__id=member.id).exists():
                sport_pass_item = SportPass.objects.get(member__id=member.id)
                sport_pass_item.code = sport_pass["code"]
                sport_pass_item.save()
            else:
                sport_pass_item = SportPass.objects.create(code=sport_pass["code"])
                member.sport_pass = sport_pass_item
                member.save()
        else:
            if SportPass.objects.filter(member__id=member.id).exists():
                sport_pass_item = SportPass.objects.get(member__id=member.id)
                sport_pass_item.delete()
        print("**********************")
        print(active_courses, waiting_courses, cancelled_courses)
        if active_courses is not None:
            active_to_remove = [
                c for c in member.active_courses.all() if c not in active_courses
            ]
            active_to_add = [
                c for c in active_courses if c not in member.active_courses.all()
            ]
            for course in active_to_add:
                member.active_courses.add(course)
            for course in active_to_remove:
                member.active_courses.remove(course)
        if waiting_courses is not None:
            waiting_to_remove = [
                c for c in member.waiting_courses.all() if c not in waiting_courses
            ]
            waiting_to_add = [
                c for c in waiting_courses if c not in member.waiting_courses.all()
            ]
            for course in waiting_to_add:
                member.waiting_courses.add(course)
            for course in waiting_to_remove:
                member.waiting_courses.remove(course)
        if cancelled_courses:
            member.cancelled_courses.clear()
            for course in cancelled_courses:
                member.cancelled_courses.add(course)
        Course.objects.manage_waiting_lists()
        return member


class MemberRetrieveSerializer(MemberSerializer):
    active_courses = CourseRetrieveSerializer(many=True)  # type:ignore[assignment]
    cancelled_courses = CourseRetrieveSerializer(many=True)  # type:ignore[assignment]
    waiting_courses = CourseRetrieveSerializer(many=True)  # type:ignore[assignment]
    season = SeasonSerializer()


class MemberRetrieveShortSerializer(MemberRetrieveSerializer):
    payment = PaymentShortSerializer(required=False, read_only=True)

    class Meta:
        model = Member
        fields = (
            "id",
            "first_name",
            "last_name",
            "ffd_license",
            "active_courses",
            "cancelled_courses",
            "waiting_courses",
            "is_validated",
            "documents",
            "payment",
        )


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
            active_courses = [
                course
                for course in self.validated_data.get("courses", [])
                if not course.is_complete
            ]
            waiting_courses = [
                course
                for course in self.validated_data.get("courses", [])
                if course.is_complete
            ]
            self._member.active_courses.add(*active_courses)
            self._member.waiting_courses.add(*waiting_courses)
            self._member.cancelled_courses.remove(*active_courses, *waiting_courses)
            self._member.save()
        elif self._action == MemberCoursesActionsEnum.REMOVE:
            for course in self.validated_data.get("courses", []):
                if self._member.waiting_courses.filter(pk=course.pk):
                    self._member.waiting_courses.remove(course)
                else:
                    self._member.cancelled_courses.add(course)
                    self._member.active_courses.remove(course)
            self._member.cancel_refund = self.validated_data.get("cancel_refund")
            self._member.save()
