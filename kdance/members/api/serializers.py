from django.contrib.auth import get_user_model
from django.db import transaction
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from members.models import (
    Course,
    Documents,
    Member,
    Payment,
    Season,
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


class MemberSerializer(WritableNestedModelSerializer, serializers.ModelSerializer):
    documents = DocumentsSerializer()

    class Meta:
        model = Member
        fields = (
            "id",
            "first_name",
            "last_name",
            "season",
            "courses",
            "documents",
            "birthday",
            "address",
            "email",
            "phone",
        )
        extra_kwargs = {"courses": {"required": False}}

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

class PaymentSerializer(serializers.ModelSerializer):
    season = SeasonSerializer()

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
            "sport_pass",
            "check",
            "other_payment",
            "comment",
            "refund",
        )
