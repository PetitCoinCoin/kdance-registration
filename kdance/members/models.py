from enum import Enum
from django.contrib.auth.models import User
from django.core.validators import EmailValidator, MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.utils import IntegrityError


class Season(models.Model):
    year = models.CharField(
        null=False,
        blank=False,
        max_length=9,
        validators=[RegexValidator(r"\d{4}-\d{4}")]
    )
    is_current = models.BooleanField(null=False, blank=False, default=True)
    discount_percent = models.PositiveIntegerField(
        default=10,
        blank=False,
        validators=[MaxValueValidator(100)],
    )
    discount_limit = models.PositiveIntegerField(
        default=2,
        blank=False,
    )

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


class CourseManager(models.Manager):
    def copy_from_season(self, from_season: int, to_season: int) -> None:
        season = Season.objects.get(id=to_season)
        for course in self.filter(season__id=from_season).values().all():
            try:
                course.pop("id")
                new_course = {
                    **course,
                    "season_id": to_season,
                }
                Course(**new_course).save()
            except IntegrityError:
                # Mettre en place un logger propre
                print("Cours non copié")


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

    objects = CourseManager()

    def __repr__(self) -> str:
        return f"{self.name} {self.season.year}"
    
    class Meta:
        unique_together = ("name", "season", "weekday", "start_hour")


class MedicEnum(Enum):
    MISSING = "Manquant"
    CERTIFICATE = "Certificat"
    TESTIMONIAL = "Attestation"


class Documents(models.Model):
    authorise_photos = models.BooleanField(null=False)
    authorise_emergency = models.BooleanField(null=False)
    medical_document = models.CharField(
        max_length=11,
        choices=[(e.value, e.value) for e in MedicEnum],
        default=MedicEnum.MISSING.value,
    )


class Payment(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cash = models.FloatField(null=False, default=0.0, validators=[MinValueValidator(0)])
    comment = models.CharField(null=False, blank=True, max_length=700, default='')
    refund = models.FloatField(null=False, default=0.0, validators=[MinValueValidator(0)])

    @property
    def due(self) -> float:
        due = 0.0
        total = 0
        members = self.user.member_set.filter(season=self.season).all()
        for member in members:
            for course in member.courses.all():
                total += 1
                due += course.price
        # Reduction
        if total >= self.season.discount_limit:
            due *= round(((100 - self.season.discount_percent) / 100), 2)
        # Adhesion
        due += len(members) * 10
        return due

    @property
    def paid(self) -> float:
        paid = self.cash - self.refund
        if hasattr(self, "sport_coupon"):
            paid += self.sport_coupon.amount
        if hasattr(self, "ancv"):
            paid += self.ancv.amount
        for other in self.other_payment.all():
            paid += other.amount
        for sport_pass in self.sport_pass.all():
            paid += sport_pass.amount
        for check in self.check_payment.all():
            paid += check.amount
        return paid


class SportCoupon(models.Model):
    amount = models.PositiveIntegerField(null=False)
    count = models.PositiveIntegerField(null=False)
    payment = models.OneToOneField(Payment, related_name="sport_coupon", on_delete=models.CASCADE)


class Ancv(models.Model):
    amount = models.PositiveIntegerField(null=False)
    count = models.PositiveIntegerField(null=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)


class SportPass(models.Model):
    amount = models.PositiveIntegerField(null=False, default=50)
    code = models.CharField(null=False, blank=False, max_length=50)
    payment = models.ForeignKey(Payment, related_name="sport_pass", on_delete=models.CASCADE)


class Check(models.Model):
    number = models.PositiveIntegerField(null=False)
    name = models.CharField(
        null=False,
        blank=False,
        max_length=100,
    )
    bank = models.CharField(
        null=False,
        blank=False,
        max_length=100,
    )
    amount = models.FloatField(null=False, validators=[MinValueValidator(0)])
    month = models.PositiveIntegerField(
        choices=[
            (1, "Janvier"),
            (2, "Février"),
            (3, "Mars"),
            (4, "Avril"),
            (5, "Mai"),
            (6, "Juin"),
            (7, "Juillet"),
            (8, "Aout"),
            (9, "Septembre"),
            (10, "Octobre"),
            (11, "Novembre"),
            (12, "Décembre"),
        ],
    )
    payment = models.ForeignKey(Payment, related_name="check_payment", on_delete=models.CASCADE)


class OtherPayment(models.Model):
    amount = models.FloatField(null=False, validators=[MinValueValidator(0)])
    comment = models.CharField(null=False, blank=False, max_length=100)
    payment = models.ForeignKey(Payment, related_name="other_payment", on_delete=models.CASCADE)


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
