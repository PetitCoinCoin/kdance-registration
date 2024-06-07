from enum import Enum

from django.contrib.auth.models import User
from django.core.validators import EmailValidator, RegexValidator
from django.db import models, transaction


class WeekdayEnum(Enum):
    MONDAY = "lundi"
    TUESDAY = "mardi"
    WEDNESDAY = "mercredi"
    THURSDAY = "jeudi"
    FRIDAY = "vendredi"


class Season(models.Model):
    year = models.CharField(
        primary_key=True,
        null=False,
        blank=False,
        max_length=9,
        validators=[RegexValidator(r"\d{4}-\d{4}")]
    )
    is_current = models.BooleanField(null=False, blank=False)

    @transaction.atomic
    def save(self, *args, **kwargs) -> None:
        # When creating a new season, we delete the older ones
        if not Season.objects.filter(year=self.year).exists():
            too_old = Season.objects.order_by("-year")[4:]
            for season in too_old:
                season.delete()
        super().save(*args, **kwargs)
        # Only one current season is possible
        if self.is_current:
            Season.objects.exclude(year=self.year).update(is_current=False)


class Teacher(models.Model):
    name = models.CharField(
        primary_key=True,
        unique=True,
        null=False,
        blank=False,
        max_length=30,
    )


class Course(models.Model):
    name = models.CharField(
        null=False,
        blank=False,
        max_length=150,
    )
    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.SET_NULL)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    price = models.PositiveIntegerField(null=False)
    weekday = models.CharField(
        choices=[(day.value, day.value) for day in WeekdayEnum],
        max_length=10,
    )
    start_hour = models.TimeField()
    end_hour = models.TimeField()


class Documents(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    authorise_photos = models.BooleanField(null=False)
    authorise_emergency = models.BooleanField(null=True)
    medical_document = models.BooleanField(null=False)


class Member(models.Model):
    first_name = models.CharField(
        blank=False,
        null=False,
        max_length=25,
    )
    last_name = models.CharField(
        blank=False,
        null=False,
        max_length=35,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course)
    documents = models.ForeignKey(Documents, null=True, on_delete=models.SET_NULL)
    birthday = models.DateField(blank=False)
    address = models.CharField(
        null=False,
        blank=False,
        max_length=500,
    )
    email = models.CharField(
        blank=False,
        null=False,
        validators=[EmailValidator()],
        max_length=150,
    )
    phone = models.CharField(
        blank=False,
        null=False,
        validators=[RegexValidator(r"\d{10}")],
        max_length=10,
    )
