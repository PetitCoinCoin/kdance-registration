from rest_framework import serializers

from members.models import (
    Course,
    Season,
    Teacher,
)

class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ("year", "is_current")


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ("name")


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "name",
            "teacher",
            "season",
            "price",
            "weekday",
            "start_hour",
            "end_hour",
        )
