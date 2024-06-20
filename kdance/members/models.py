from django.contrib.auth.models import User
from django.core.validators import EmailValidator, RegexValidator
from django.db import models, transaction


class Season(models.Model):
    year = models.CharField(
        null=False,
        blank=False,
        max_length=9,
        validators=[RegexValidator(r"\d{4}-\d{4}")]
    )
    is_current = models.BooleanField(null=False, blank=False, default=True)

    @transaction.atomic
    def save(self, *args, **kwargs) -> None:
        created = self.pk is None
        # When creating a new season, we delete the older ones
        if not Season.objects.filter(year=self.year).exists():
            too_old = Season.objects.order_by("-year")[4:]
            for season in too_old:
                season.delete()
        super().save(*args, **kwargs)
        # Only one current season is possible
        if self.is_current:
            Season.objects.exclude(year=self.year).update(is_current=False)
        # At creation, we add Payment object for each User
        if created:
            for user in User.objects.all():
                Payment(user=user, season=self).save()

    def __repr__(self) -> str:
        return self.year


class Teacher(models.Model):
    name = models.CharField(
        unique=True,
        null=False,
        blank=False,
        max_length=30,
    )

    def __repr__(self) -> str:
        return self.name


class Course(models.Model):
    name = models.CharField(
        null=False,
        blank=False,
        max_length=150,
    )
    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.SET_NULL)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    price = models.PositiveIntegerField(null=False)
    weekday = models.PositiveIntegerField(
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
    start_hour = models.TimeField()
    end_hour = models.TimeField()

    def __repr__(self) -> str:
        return f"{self.name} {self.season.year}"
    
    class Meta:
        unique_together = ("name", "season", "weekday", "start_hour")


class Documents(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    authorise_photos = models.BooleanField(null=False)
    authorise_emergency = models.BooleanField(null=True)
    medical_document = models.BooleanField(null=False)


class Payment(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paid = models.PositiveIntegerField(null=False, default=0)

    @property
    def due(self) -> float:
        due = 0.0
        total = 0
        members = self.user.member_set.filter(is_active=True, season=self.season).all()
        for member in members:
            for course in member.courses.all():
                total += 1
                due += course.price
        # Reduction
        if total > 1:
            due *= 0.9
        # Adhesion
        due += len(members) * 10
        return due


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
    is_active = models.BooleanField(
        default=True,
        null=False,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
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

    def __repr__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Meta:
        unique_together = ("first_name", "last_name", "user", "season")
