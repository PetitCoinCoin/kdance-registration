import logging

from enum import Enum

from django.contrib.auth.models import User
from django.core.validators import EmailValidator, MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.db.utils import IntegrityError
from django.dispatch import receiver

_logger = logging.getLogger(__name__)

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
        if created and Season.objects.count() > 4:
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

    def save(self, *args, **kwargs) -> None:
        self.name = self.name.title()
        super().save(*args, **kwargs)


class CourseManager(models.Manager):
    def copy_from_season(self, from_season: int, to_season: int) -> None:
        for course in self.filter(season__id=from_season).values().all():
            try:
                course.pop("id")
                new_course = {
                    **course,
                    "season_id": to_season,
                }
                Course(**new_course).save()
            except IntegrityError:
                _logger.info("Cours non copié")


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


class OtherPayment(models.Model):
    amount = models.FloatField(null=False, validators=[MinValueValidator(0)])
    comment = models.CharField(null=False, blank=False, max_length=100)


class Payment(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cash = models.FloatField(null=False, default=0.0, validators=[MinValueValidator(0)])
    other_payment = models.OneToOneField(OtherPayment, null=True, on_delete=models.SET_NULL)
    comment = models.CharField(null=False, blank=True, max_length=700, default='')
    refund = models.FloatField(null=False, default=0.0, validators=[MinValueValidator(0)])
    special_discount = models.FloatField(null=False, default=0.0, validators=[MinValueValidator(0)])

    @property
    def due(self) -> float:
        due = 0.0
        total = 0
        members = self.user.member_set.filter(season=self.season).all()
        for member in members:
            for course in member.courses:
                total += 1
                due += course.price
        # Discount
        due -= self.special_discount
        if total >= self.season.discount_limit:
            due *= round(((100 - self.season.discount_percent) / 100), 2)
        # Adhesion and license
        due += len(members) * 10
        due += sum([member.ffd_license for member in members])
        # Refund after cancellation
        due -= sum(member.cancel_refund for member in members)
        return due

    @property
    def due_detail(self) -> list[str]:
        members_count = 0
        courses_count = 0
        courses_price = 0
        members = self.user.member_set.filter(season=self.season).all()
        for member in members:
            members_count += 1
            for course in member.courses:
                courses_count += 1
                courses_price += course.price
        discount = 0
        if courses_count > self.season.discount_limit:
            discount = round((courses_price * self.season.discount_percent / 100), 2)
        licenses = [member.ffd_license for member in members if member.ffd_license > 0]
        license_count = len(licenses)
        license_price = sum(licenses)
        cancelled = sum(member.cancel_refund for member in members)
        info = [
            f"{members_count} adhésion(s): {10 * members_count}€",
            f"{courses_count} cours: {courses_price}€",
        ]
        if discount:
            info.append(f"Remise de {self.season.discount_percent}% sur les cours: -{discount}€")
        if license_price:
            info.append(f"{license_count} licence(s): {license_price}€")
        if cancelled:
            info.append(f"Annulation(s): -{cancelled}€")
        return info

    @property
    def paid(self) -> float:
        paid = self.cash
        if hasattr(self, "sport_coupon"):
            paid += self.sport_coupon.amount
        if hasattr(self, "ancv"):
            paid += self.ancv.amount
        if self.other_payment is not None:
            paid += self.other_payment.amount
        for check in self.check_payment.all():
            paid += check.amount
        for member in Member.objects.filter(user=self.user, season=self.season).all():
            if member.sport_pass:
                paid += member.sport_pass.amount
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


class PersonModel(models.Model):
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

    class Meta:
        abstract = True

    def __repr__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs) -> None:
        self.first_name = self.first_name.title()
        self.last_name = self.last_name.title()
        self.email = self.email.lower()
        super().save(*args, **kwargs)


class ContactManager(models.Manager):
    def clean_orphan(self) -> None:
        """If contact is linked to no one, we delete it."""
        for contact in self.all():
            if not contact.member_set.all():  # type:ignore[attr-defined]
                contact.delete()


class Contact(PersonModel):
    class ContactEnum(models.TextChoices):
        RESPONSIBLE = "responsible", "Responsable légal"
        EMERGENCY = "emergency", "Contact d'urgence"

    contact_type = models.CharField(
        max_length=17,
        choices= ContactEnum.choices,
    )
    objects = ContactManager()


class Member(PersonModel):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active_courses = models.ManyToManyField(Course, related_name="members")
    cancelled_courses = models.ManyToManyField(Course, related_name="members_cancelled")
    contacts = models.ManyToManyField(Contact)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    documents = models.OneToOneField(Documents, null=True, on_delete=models.SET_NULL)
    birthday = models.DateField(blank=False)
    address = models.CharField(
        null=False,
        blank=False,
        max_length=500,
    )
    sport_pass = models.OneToOneField(SportPass, null=True, on_delete=models.SET_NULL)
    cancel_refund = models.FloatField(null=False, default=0.0, validators=[MinValueValidator(0)])
    ffd_license = models.PositiveIntegerField(
        choices=[
            (0, "Aucune"),
            (19, "Licence A Loisir"),
            (21, "Licence B Compétiteur"),
            (38, "Licence C Compétiteur national"),
            (50, "Licence D Compétiteur international"),
        ],
        default=0,
    )

    class Meta:
        unique_together = ("first_name", "last_name", "user", "season")

    @property
    def payment(self) -> Payment:
        return Payment.objects.get(user=self.user, season=self.season)

    @property
    def courses(self) -> list:
        return list(self.active_courses.all()) + list(self.cancelled_courses.all())

@receiver(post_delete, sender=Member)
def post_delete_documents(sender, instance, *args, **kwargs):
    if instance.documents:
        instance.documents.delete()
