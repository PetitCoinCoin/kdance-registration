import logging

from enum import Enum
from datetime import date

from members.emails import EmailEnum, EmailSender
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import (
    EmailValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models, transaction
from django.db.models import Count, Q
from django.db.models.signals import post_delete
from django.db.utils import IntegrityError
from django.dispatch import receiver
from solo.models import SingletonModel

_logger = logging.getLogger(__name__)


class GeneralSettings(SingletonModel):
    allow_signup = models.BooleanField(
        null=False,
        default=True,
    )
    allow_new_member = models.BooleanField(
        null=False,
        default=True,
    )
    pre_signup_payment_delta_days = models.PositiveBigIntegerField(
        null=False, default=7
    )


class Season(models.Model):
    SEASON_COUNT = 5

    year = models.CharField(
        null=False,
        blank=False,
        max_length=9,
        validators=[RegexValidator(r"\d{4}-\d{4}")],
    )
    is_current = models.BooleanField(null=False, blank=False, default=True)
    pre_signup_start = models.DateField(null=False, blank=False)
    pre_signup_end = models.DateField(null=False, blank=False)
    signup_start = models.DateField(null=True)
    signup_end = models.DateField(null=True)
    discount_percent = models.PositiveIntegerField(
        default=10,
        blank=False,
        validators=[MaxValueValidator(100)],
    )
    discount_limit = models.PositiveIntegerField(
        default=2,
        blank=False,
    )
    pass_sport_amount = models.PositiveIntegerField(
        default=50,
        blank=False,
    )
    ffd_a_amount = models.PositiveIntegerField(
        blank=False, verbose_name="Licence A Loisir price"
    )
    ffd_b_amount = models.PositiveIntegerField(
        blank=False, verbose_name="Licence B Compétiteur price"
    )
    ffd_c_amount = models.PositiveIntegerField(
        blank=False, verbose_name="Licence C Compétiteur national price"
    )
    ffd_d_amount = models.PositiveIntegerField(
        blank=False, verbose_name="Licence D Compétiteur international price"
    )

    @transaction.atomic
    def save(self, *args, **kwargs) -> None:
        created = self.pk is None
        # When creating a new season, we delete the older ones
        if created and Season.objects.count() >= self.SEASON_COUNT:
            too_old = Season.objects.order_by("-year")[self.SEASON_COUNT - 1 :]
            for season in too_old:
                season.delete()
        # When editing, we need to check if FFD amounts were updated
        prev_state = None
        if not created and self.is_current:
            prev_state = Season.objects.get(pk=self.pk)
        super().save(*args, **kwargs)
        # Only one current season is possible
        if self.is_current:
            Season.objects.exclude(year=self.year).update(is_current=False)
        # At creation, we add Payment object for each User
        if created:
            for user in User.objects.exclude(username=settings.SUPERUSER_EMAIL).all():
                Payment(user=user, season=self).save()
        # If FFD amounts were updated, members need to be updated
        for attr in ("ffd_a_amount", "ffd_b_amount", "ffd_c_amount", "ffd_d_amount"):
            if prev_state and getattr(prev_state, attr) != getattr(self, attr):
                Member.objects.filter(ffd_license=getattr(prev_state, attr)).update(
                    ffd_license=getattr(self, attr)
                )

    @property
    def previous_season(self) -> str:
        previous_season = (
            Season.objects.filter(year__lt=self.year).order_by("-year").first()
        )
        return previous_season.year if previous_season else ""

    @property
    def is_before_pre_signup(self) -> bool:
        return date.today() <= self.pre_signup_end

    @property
    def is_pre_signup_ongoing(self) -> bool:
        today = date.today()
        return self.pre_signup_start <= today <= self.pre_signup_end

    @property
    def is_before_signup(self) -> bool:
        return (
            self.signup_start is not None
            and self.signup_end is not None
            and date.today() <= self.signup_end
        )

    @property
    def is_signup_ongoing(self) -> bool:
        if not self.signup_start or not self.signup_end:
            return False
        today = date.today()
        return self.signup_start <= today <= self.signup_end

    @property
    def is_after_signup(self) -> bool:
        return (
            self.signup_start is not None
            and self.signup_end is not None
            and date.today() > self.signup_end
        )

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

    def manage_waiting_lists(self):
        if not GeneralSettings.get_solo().allow_new_member:
            return
        current_season = Season.objects.get(is_current=True)
        for course in self.filter(season__id=current_season.id):
            course.update_queue()


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
    capacity = models.PositiveIntegerField(null=False, default=12)

    objects = CourseManager()

    def __repr__(self) -> str:
        return f"{self.name} {self.season.year}"

    def __str__(self) -> str:
        return f"{self.name}, {self.get_weekday_display()} - {self.season.year}"

    class Meta:
        unique_together = ("name", "season", "weekday", "start_hour")

    @property
    def is_complete(self) -> bool:
        return self.members.count() >= self.capacity

    @property
    def waiting(self) -> int:
        return self.members_waiting.count()

    @transaction.atomic
    def save(self, *args, **kwargs) -> None:
        is_edit = self.pk is not None
        super().save(*args, **kwargs)
        if is_edit and GeneralSettings.get_solo().allow_new_member:
            self.update_queue()

    def update_queue(self) -> None:
        if self.members_waiting.count() and not self.is_complete:
            member: Member = self.members_waiting.order_by("created").first()  # type: ignore
            member.active_courses.add(self)
            member.waiting_courses.remove(self)
            member.save()
            email_sender = EmailSender(EmailEnum.WAITING_TO_ACTIVE_COURSE)
            email_sender.send_email(
                emails=[member.email, member.user.username],
                full_name=f"{member.first_name} {member.last_name}",
                course_name=self.name,
                weekday=self.get_weekday_display(),
                start_hour=self.start_hour.strftime("%Hh%M"),
            )


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
    other_payment = models.OneToOneField(
        OtherPayment, null=True, on_delete=models.SET_NULL
    )
    comment = models.CharField(null=False, blank=True, max_length=700, default="")
    refund = models.FloatField(
        null=False, default=0.0, validators=[MinValueValidator(0)]
    )
    special_discount = models.FloatField(
        null=False, default=0.0, validators=[MinValueValidator(0)]
    )

    @property
    def sport_pass_count(self) -> int:
        count = 0
        for member in self.user.member_set.filter(season=self.season).all():
            if member.sport_pass:
                count += 1
        return count

    @property
    def sport_pass_amount(self) -> int:
        amount = 0
        for member in self.user.member_set.filter(season=self.season).all():
            if member.sport_pass:
                amount += member.sport_pass.amount
        return amount

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
            due *= (100 - self.season.discount_percent) / 100
        # Adhesion and license
        validated_members = members.annotate(
            num_courses=Count("active_courses")
        ).filter(Q(num_courses__gt=0) | Q(is_validated=True))
        due += validated_members.count() * 10
        due += sum([member.ffd_license for member in validated_members])
        # Refund after cancellation
        due -= sum(member.cancel_refund for member in members)
        return int(round(due))

    @property
    def due_detail(self) -> list[str]:
        members_count = 0
        courses_count = 0
        courses_price = 0
        members = self.user.member_set.filter(season=self.season).all()
        for member in members:
            if member.is_validated or member.courses:
                members_count += 1
            for course in member.courses:
                courses_count += 1
                courses_price += course.price
        discount = 0
        if courses_count >= self.season.discount_limit:
            discount = int(round(courses_price * self.season.discount_percent / 100))
        licenses = [
            member.ffd_license
            for member in members
            if member.ffd_license > 0 and (member.is_validated or member.courses)
        ]
        license_count = len(licenses)
        license_price = sum(licenses)
        cancelled = sum(member.cancel_refund for member in members)
        info = [
            f"{members_count} adhésion(s): {10 * members_count}€",
            f"{courses_count} cours: {courses_price}€",
        ]
        if discount:
            info.append(
                f"Remise de {self.season.discount_percent}% sur les cours: -{discount}€"
            )
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
        if hasattr(self, "cb_payment"):
            paid += self.cb_payment.amount
        if self.other_payment is not None:
            paid += self.other_payment.amount
        for check in self.check_payment.all():
            paid += check.amount
        for member in Member.objects.filter(user=self.user, season=self.season).all():
            if member.sport_pass:
                paid += member.sport_pass.amount
        return paid

    @transaction.atomic
    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        if self.paid >= self.due:
            for member in Member.objects.filter(
                user=self.user, season=self.season, is_validated=False
            ).all():
                member.is_validated = True
                member.save()


class CBPayment(models.Model):
    amount = models.FloatField(null=False, validators=[MinValueValidator(0)])
    transaction_type = models.CharField(
        null=False, blank=True, max_length=10, default=""
    )
    payment = models.OneToOneField(
        Payment, related_name="cb_payment", on_delete=models.CASCADE
    )


class SportCoupon(models.Model):
    amount = models.PositiveIntegerField(null=False)
    count = models.PositiveIntegerField(null=False)
    payment = models.OneToOneField(
        Payment, related_name="sport_coupon", on_delete=models.CASCADE
    )


class Ancv(models.Model):
    amount = models.PositiveIntegerField(null=False)
    count = models.PositiveIntegerField(null=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)


class SportPass(models.Model):
    code = models.CharField(null=False, blank=False, max_length=50)

    @property
    def amount(self) -> int:
        return self.member.season.pass_sport_amount


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
    payment = models.ForeignKey(
        Payment, related_name="check_payment", on_delete=models.CASCADE
    )


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
            if not contact.member_set.all():  # type: ignore[attr-defined]
                contact.delete()


class Contact(PersonModel):
    class ContactEnum(models.TextChoices):
        RESPONSIBLE = "responsible", "Responsable légal"
        EMERGENCY = "emergency", "Contact d'urgence"

    contact_type = models.CharField(
        max_length=17,
        choices=ContactEnum.choices,
    )
    objects = ContactManager()


class MemberManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user__isnull=False)


class Member(PersonModel):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    active_courses = models.ManyToManyField(Course, related_name="members")
    waiting_courses = models.ManyToManyField(Course, related_name="members_waiting")
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
    postal_code = models.CharField(
        null=False,
        blank=False,
        max_length=5,
    )
    city = models.CharField(
        null=False,
        blank=False,
        max_length=40,
    )
    sport_pass = models.OneToOneField(SportPass, null=True, on_delete=models.SET_NULL)
    cancel_refund = models.FloatField(
        null=False, default=0.0, validators=[MinValueValidator(0)]
    )
    ffd_license = models.PositiveIntegerField(default=0)
    is_validated = models.BooleanField(default=False, null=False)
    created = models.DateTimeField(auto_now_add=True)

    objects = MemberManager()

    class Meta:
        unique_together = ("first_name", "last_name", "user", "season")

    @property
    def payment(self) -> Payment:
        return Payment.objects.get(user=self.user, season=self.season)

    @property
    def courses(self) -> list:
        return list(self.active_courses.all()) + list(self.cancelled_courses.all())

    @property
    def full_address(self) -> str:
        return f"{self.address}, {self.postal_code} {self.city}"


@receiver(post_delete, sender=Member)
def post_delete_member(sender, instance, *args, **kwargs):
    if instance.documents:
        instance.documents.delete()
    if instance.sport_pass:
        instance.sport_pass.delete()
    Course.objects.manage_waiting_lists()
