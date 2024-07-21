from django.contrib.auth import get_user_model
from django.db import transaction
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from members.models import (
    Ancv,
    Check,
    Contact,
    Course,
    Documents,
    Member,
    Payment,
    Season,
    SportCoupon,
    SportPass,
    Teacher,
)

User = get_user_model()

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
            raise serializers.ValidationError("Cette saison n'existe pas")
        return season_id

    @staticmethod
    def validate_to_season(season_id: int) -> int:
        if not Season.objects.filter(id=season_id).exists():
            raise serializers.ValidationError("Cette saison n'existe pas")
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
        if not validated.get("email", "") and validated.get("contact_type") == Contact.ContactEnum.RESPONSIBLE.value:
            raise serializers.ValidationError({"email": "L'email est obligatoire pour le responsable."})
        return validated


class AncvSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ancv
        fields = ("amount", "count")


class SportCouponSerializer(serializers.ModelSerializer):

    class Meta:
        model = SportCoupon
        fields = ("amount", "count")


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
    ancv = AncvSerializer()
    sport_coupon = SportCouponSerializer()
    check_payment = CheckSerializer(many=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "season",
            "paid",
            "due",
            "cash",
            "sport_coupon",
            "ancv",
            "check_payment",
            "other_payment",
            "comment",
            "refund",
        )

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
    courses = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Course.objects.all(),
        default=list,
    )

    class Meta:
        model = Member
        fields = (
            "id",
            "first_name",
            "last_name",
            "season",
            "courses",
            "contacts",
            "documents",
            "payment",
            "sport_pass",
            "birthday",
            "address",
            "email",
            "phone",
            "ffd_license",
        )

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        if validated.get("courses", []):
            for course in validated.get("courses", []):
                if course.season.id != validated["season"].id:
                    raise serializers.ValidationError("Un cours ne correspond pas à la saison.")
        return validated

    @transaction.atomic
    def save(self, **kwargs: Member) -> None:
        username = kwargs.get("user")
        self.validated_data["user"] = User.objects.get(username=username)
        contacts = self.validated_data.pop("contacts", None)
        documents = self.validated_data.pop("documents", None) if self.partial else None
        member = super().save()
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
    courses = CourseRetrieveSerializer(many=True)
    season = SeasonSerializer()
