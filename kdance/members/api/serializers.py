from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from members.models import (
    Course,
    Member,
    Payment,
    Season,
    Teacher,
)

User = get_user_model()

class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ("id", "year", "is_current")


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


class MemberSerializer(serializers.ModelSerializer):

    class Meta:
        model = Member
        fields = (
            "first_name",
            "last_name",
            "courses",
            "documents",
            "birthday",
            "address",
            "email",
            "phone",
        )

    @transaction.atomic
    def save(self, **kwargs) -> None:
        username = kwargs.get("user")
        self.validated_data["user"] = User.objects.get(username=username)
        super().save()


class PaymentSerializer(serializers.ModelSerializer):
    season = SeasonSerializer()

    class Meta:
        model = Payment
        fields = ("season", "paid", "due")


class MemberSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True)

    class Meta:
        model = Member
        fields = (
            "first_name",
            "last_name",
            "courses",
            "documents",
            "birthday",
            "address",
            "email",
            "phone",
        )
