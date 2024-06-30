from django.contrib.auth import get_user_model
from django.db import transaction
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from members.models import (
    Ancv,
    Check,
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
    payment = PaymentSerializer()
    sport_pass = SportPassSerializer()

    class Meta:
        model = Member
        fields = (
            "id",
            "first_name",
            "last_name",
            "season",
            "courses",
            "documents",
            "payment",
            "sport_pass",
            "birthday",
            "address",
            "email",
            "phone",
        )
        extra_kwargs = {
            "courses": {"required": False},
            "payment": {"read_only": True},
            "sport_pass": {"required": False},
        }

    def validate(self, attr: dict) -> dict:
        validated = super().validate(attr)
        if validated.get("courses", []):
            for course in validated.get("courses", []):
                if course.season.id != validated["season"].id:
                    raise serializers.ValidationError("Un cours ne correspond pas à la saison.")
        return validated

    @transaction.atomic
    def save(self, **kwargs) -> None:
        username = kwargs.get("user")
        self.validated_data["user"] = User.objects.get(username=username)
        super().save()


class MemberRetrieveSerializer(MemberSerializer):
    courses = CourseRetrieveSerializer(many=True)
    season = SeasonSerializer()
