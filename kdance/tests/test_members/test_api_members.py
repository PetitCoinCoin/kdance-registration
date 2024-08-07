"""Tests related to Members API view."""
import pytest

from datetime import datetime, time, timezone

from django.urls import reverse
from parameterized import parameterized

from members.api.views import MemberViewSet
from members.models import (
    Course,
    Documents,
    Member,
    Season,
)
from tests.authentication import AuthenticatedAction, AuthTestCase


@pytest.mark.django_db
class TestMembersApiView(AuthTestCase):
    view_function = MemberViewSet
    _kwargs = {}

    _member: Member | None = None
    _season: Season | None = None

    @pytest.fixture(autouse=True)
    def set_member(self):
        season, _ = Season.objects.get_or_create(year="1900-1901")
        self._season = season
        doc, _ = Documents.objects.get_or_create(
            authorise_photos=False,
            authorise_emergency=False,
        )
        member, _ = Member.objects.get_or_create(
            user=self.testuser,
            season=season,
            first_name="Plip",
            last_name="Plop",
            birthday=datetime(1900, 5, 1, tzinfo=timezone.utc),
            address="Par ici",
            email="plip@plop.fr",
            phone="0987654321",
            documents=doc,
        )
        self._member = member

    @property
    def view_url(self):
        return reverse(
            f"api-members-{'detail' if 'pk' in self._kwargs else 'list'}",
            kwargs=self._kwargs,
        )

    @parameterized.expand([
        ("get", 200, 200, False),
        ("get", 200, 200, True),
        ("post", 400, 400, False),
        ("put", 403, 405, True),
        ("patch", 200, 200, True),
    ])
    def test_permissions(self, method, user_status, superuser_status, with_pk):
        self._kwargs = {"pk": self._member.pk} if with_pk else {}
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )

    def test_delete_permissions(self):
        def gen_pk():
            val = 0
            new_member = Member.objects.create(
                user=self.testuser,
                season=self._season,
                first_name=f"Plip{val}",
                last_name="Plop",
                birthday=datetime(1900, 1, 10 + val, tzinfo=timezone.utc),
                address="Par ici",
                email="plip@plop.fr",
                phone="0987654321",
            )
            yield new_member.pk
            val += 1

        assert self.users_have_permission(
            urls=(reverse("api-members-detail", args=[next(gen_pk())]), self.view_function),
            method="delete",
            user_status=403,
            superuser_status=204,
        )

    @parameterized.expand([
        ("get", False),
        ("get", True),
        ("post", False),
        ("put", True),
        ("patch", True),
        ("delete", True),
    ])
    def test_authentication_mandatory(self, method, with_pk):
        self._kwargs = {"pk": self._member.pk} if with_pk else {}
        assert self.authentication_is_mandatory(method)

    @parameterized.expand([
        (200, False, False),
        (200, True, False),
        (403, False, True),
    ])
    def test_get_permissions_limitations(self, status_code, with_pk, with_super_pk):
        """Tests that GET requests are allowed for simple user, but with limited results."""
        super_member, _ = Member.objects.get_or_create(
            user=self.super_testuser,
            season=self._season,
            first_name="Superplip",
            last_name="Superplop",
            birthday=datetime(1900, 10, 1, tzinfo=timezone.utc),
            address="Par ici",
            email="superplip@plop.fr",
            phone="0987654321",
        )
        assert Member.objects.count() == 2
        self._kwargs = {}
        if with_pk:
            self._kwargs["pk"] = self._member.pk
        if with_super_pk:
            self._kwargs["pk"] = super_member.pk
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == status_code, response
            if status_code == 200:
                response_json = response.json()
                if not with_pk and not with_super_pk:
                    assert len(response_json) == 1
                    assert response_json[0]["id"] == self._member.pk
                else:
                    assert response_json["id"] == self._member.pk

    @parameterized.expand([
        (200, True, False),
        (403, False, True),
    ])
    def test_patch_permissions_limitations(self, status_code, with_pk, with_super_pk):
        """Tests that PATCH request are allowed for simple user, but only for their members."""
        super_member, _ = Member.objects.get_or_create(
            user=self.super_testuser,
            season=self._season,
            first_name="Superplip",
            last_name="Superplop",
            birthday=datetime(1900, 10, 1, tzinfo=timezone.utc),
            address="Par ici",
            email="superplip@plop.fr",
            phone="0987654321",
        )
        assert Member.objects.count() == 2
        if with_pk:
            self._kwargs["pk"] = self._member.pk
        if with_super_pk:
            self._kwargs["pk"] = super_member.pk
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.patch(self.view_url, data={"first_name": "Plup"}, content_type="application/json")
            assert response.status_code == status_code, response
            if status_code == 200:
                response_json = response.json()
                assert response_json["id"] == self._member.pk
                assert response_json["first_name"] == "Plup"

    @parameterized.expand([
        ("Jean-Mich", "Jean-Mich", "Pouet", "Pouet", "j@m.com", "j@m.com"),
        ("jean-mich", "Jean-Mich", "pouet", "Pouet", "J@M.com", "j@m.com"),
        ("JEAN-MICH", "Jean-Mich", "POUET", "Pouet", "J@M.COM", "j@m.com"),
    ])
    def test_post(self, first_name, exp_first_name, last_name, exp_last_name, email, exp_email):
        """Tests creation with data formating."""
        data = {
            "season": self._season.pk,
            "first_name": first_name,
            "last_name": last_name,
            "birthday": "1900-12-24",
            "address": "Par ici",
            "email": email,
            "phone": "0987654321",
            "sport_pass": {
                "code": "AZE-AZE-AZE",
                "amount": 50,
            },
            "contacts": [],
            "documents": {
                "authorise_photos": False,
                "authorise_emergency": True,
                "medical_document": "Manquant",
            }
        }
        self._kwargs = {}
        assert Member.objects.count() == 1
        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.post(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 201, response
            response_json = response.json()
            assert response_json["first_name"] == exp_first_name
            assert response_json["last_name"] == exp_last_name
            assert response_json["email"] == exp_email
        assert Member.objects.count() == 2
        new_member = Member.objects.filter(
            user=self.testuser,
            first_name=exp_first_name,
            last_name=exp_last_name,
            email=exp_email,
            season=self._season,
        ).first()
        assert new_member is not None
        assert Documents.objects.count() == 2
        assert Documents.objects.filter(member__id=new_member.pk)

    @parameterized.expand([
        ("Plip", "Plop", None, None, None, None, "first_name", "Cet adhérent existe déjà pour la saison."),
        ("plip", "PLOP", None, None, None, None, "last_name", "Cet adhérent existe déjà pour la saison."),
        ("", "Pouet", None, None, None, None, "first_name", "Ce champ ne peut être vide."),
        ("Jean-Mich", "", None, None, None, None, "last_name", "Ce champ ne peut être vide."),
        (None, None, "jm.com", None, None, None, "email", "Saisissez une adresse e-mail valide."),
        (None, None, "", None, None, None, "email", "Ce champ ne peut être vide."),
        (None, None, None, "+331234", None, None, "phone", "Saisissez une valeur valide."),
        (None, None, None, "", None, None, "phone", "Ce champ ne peut être vide."),
        (None, None, None, None, "", None, "address", "Ce champ ne peut être vide."),
        (None, None, None, None, None, "24/12/2000", "birthday", "La date n'a pas le bon format. Utilisez un des formats suivants\xa0: YYYY-MM-DD."),
        (None, None, None, None, None, "", "birthday", "La date n'a pas le bon format. Utilisez un des formats suivants\xa0: YYYY-MM-DD."),
    ])
    def test_post_payload_error(self, first_name, last_name, email, phone, address, birthday, key, message):
        data = {
            "user": self.testuser.pk,
            "season": self._season.pk,
            "first_name": "Jean-Mich",
            "last_name": "Pouet",
            "birthday": "1900-12-24",
            "address": "Par ici",
            "email": "j@m.com",
            "phone": "0987654321",
            "contacts": [],
            "documents": {
                "authorise_photos": False,
                "authorise_emergency": True,
                "medical_document": "Manquant",
            }
        }
        if first_name is not None:
            data["first_name"] = first_name
        if last_name is not None:
            data["last_name"] = last_name
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        if address is not None:
            data["address"] = address
        if birthday is not None:
            data["birthday"] = birthday
        self._kwargs = {}
        assert Member.objects.count() == 1

        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.post(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 400, response
            response_json = response.json()
            assert message in response_json[key]
        assert Member.objects.count() == 1

    @parameterized.expand([
        ("Jean", "Mich", "j@m.com", "0123456789", "Par là", "2000-01-31", "Certificat"),
        ("Jean", "Mich", None, None, None, None, None),
        (None, None, "j@m.com", "0123456789", "Par là", None, None),
        (None, None, None, None, None, "2000-01-31", None),
        (None, None, None, None, None, None, "Attestation"),
    ])
    def test_patch(self, first_name, last_name, email, phone, address, birthday, doc):
        data = {}
        if first_name is not None:
            data["first_name"] = first_name
        if last_name is not None:
            data["last_name"] = last_name
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        if address is not None:
            data["address"] = address
        if birthday is not None:
            data["birthday"] = birthday
        if doc is not None:
            data["documents"] = {"medical_document": doc}
        self._kwargs["pk"] = self._member.pk
        assert Member.objects.count() == 1

        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.patch(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 200, response
        assert Member.objects.count() == 1
        if first_name is not None:
            assert Member.objects.filter(first_name=first_name).exists()
        if last_name is not None:
            assert Member.objects.filter(last_name=last_name).exists()
        if email is not None:
            assert Member.objects.filter(email=email).exists()
        if phone is not None:
            assert Member.objects.filter(phone=phone).exists()
        if address is not None:
            assert Member.objects.filter(address=address).exists()
        if birthday is not None:
            assert Member.objects.filter(birthday=datetime.strptime(birthday, "%Y-%m-%d")).exists()
        if doc is not None:
            assert Member.objects.filter(documents__medical_document=doc).exists()

    @parameterized.expand([
        ("", "Pouet", None, None, None, None, "first_name", "Ce champ ne peut être vide."),
        ("Jean-Mich", "", None, None, None, None, "last_name", "Ce champ ne peut être vide."),
        (None, None, "jm.com", None, None, None, "email", "Saisissez une adresse e-mail valide."),
        (None, None, "", None, None, None, "email", "Ce champ ne peut être vide."),
        (None, None, None, "+331234", None, None, "phone", "Saisissez une valeur valide."),
        (None, None, None, "", None, None, "phone", "Ce champ ne peut être vide."),
        (None, None, None, None, "", None, "address", "Ce champ ne peut être vide."),
        (None, None, None, None, None, "24/12/2000", "birthday", "La date n'a pas le bon format. Utilisez un des formats suivants\xa0: YYYY-MM-DD."),
        (None, None, None, None, None, "", "birthday", "La date n'a pas le bon format. Utilisez un des formats suivants\xa0: YYYY-MM-DD."),
    ])
    def test_patch_payload_error(self, first_name, last_name, email, phone, address, birthday, key, message):
        data = {}
        if first_name is not None:
            data["first_name"] = first_name
        if last_name is not None:
            data["last_name"] = last_name
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        if address is not None:
            data["address"] = address
        if birthday is not None:
            data["birthday"] = birthday
        self._kwargs["pk"] = self._member.pk
        assert Member.objects.count() == 1

        with AuthenticatedAction(self.client, self.testuser):
            response = self.client.patch(self.view_url, data=data, content_type="application/json")
            assert response.status_code == 400, response
            response_json = response.json()
            assert message in response_json[key]
        assert Member.objects.count() == 1

    def test_delete(self):
        self._kwargs["pk"] = self._member.pk
        assert Member.objects.count() == 1
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.delete(self.view_url)
            assert response.status_code == 204, response
        assert Member.objects.count() == 0


@pytest.mark.django_db
class TestMembersCoursesApiView(AuthTestCase):
    view_function = MemberViewSet
    _kwargs = {}

    _member: Member | None = None
    _season: Season | None = None

    @pytest.fixture(autouse=True)
    def set_member(self):
        season, _ = Season.objects.get_or_create(year="1900-1901")
        self._season = season
        member, _ = Member.objects.get_or_create(
            user=self.testuser,
            season=season,
            first_name="Plip",
            last_name="Plop",
            birthday=datetime(1900, 5, 1, tzinfo=timezone.utc),
            address="Par ici",
            email="plip@plop.fr",
            phone="0987654321",
        )
        self._member = member

    def set_course(self):
        return Course.objects.create(
            name="Cha cha cha",
            season=self._season,
            price=10,
            weekday=0,
            start_hour=time(10, 0),
            end_hour=time(11, 0),
        )

    @property
    def view_url(self):
        self._kwargs["pk"] = self._member.pk
        return reverse("api-members-courses", kwargs=self._kwargs)

    @parameterized.expand([
        ("get", 405, 405),
        ("post", 405, 405),
        ("put", 403, 200),
        ("patch", 405, 405),
        ("delete", 403, 405),
    ])
    def test_permissions(self, method, user_status, superuser_status):
        self._kwargs["action"] = "add"
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
        )
        self._kwargs["action"] = "remove"
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
            data={"cancel_refund": 0},
            content_type="application/json",
        )

    @parameterized.expand([
        "get", "post", "put", "patch", "delete"
    ])
    def test_authentication_mandatory(self, method):
        self._kwargs["action"] = "add"
        assert self.authentication_is_mandatory(method)
        self._kwargs["action"] = "remove"
        assert self.authentication_is_mandatory(method)

    def test_add(self):
        course = self.set_course()
        self._kwargs["action"] = "add"
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.put(
                self.view_url,
                data={"courses": [course.pk]},
                content_type="application/json",
            )
            assert response.status_code == 200, response
        self._member.refresh_from_db()
        assert course in self._member.active_courses.all()

    def test_remove(self):
        course = self.set_course()
        self._member.active_courses.add(course)
        self._member.refresh_from_db()
        assert len(self._member.active_courses.all()) == 1
        self._kwargs["action"] = "remove"
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.put(
                self.view_url,
                data={"courses": [course.pk], "cancel_refund": 5},
                content_type="application/json",
            )
            assert response.status_code == 200, response
        self._member.refresh_from_db()
        assert not len(self._member.active_courses.all())
        assert course in self._member.cancelled_courses.all()

    @parameterized.expand([
        (1000000, None, "add", "courses", 400, "l'objet n'existe pas."),
        (1000000, None, "remove", "courses", 400, "l'objet n'existe pas."),
        (None, 10, "add", "cancel_refund", 400, "Ce champ ne doit pas être modifié pour ajouter un cours."),
        (None, None, "remove", "cancel_refund", 400, "Ce champ est obligatoire pour retirer un cours."),
        (None, None, "blob", "", 404, ""),
    ])
    def test_action_error(self, course_pk, refund, action, key, status_code, message):
        course = self.set_course()
        data = {
            "courses": [course_pk or course.pk],
        }
        if refund is not None:
            data["cancel_refund"] = refund
        self._kwargs["action"] = action
        init_active = len(self._member.active_courses.all())
        init_cancelled = len(self._member.cancelled_courses.all())
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.put(
                self.view_url,
                data=data,
                content_type="application/json",
            )
            assert response.status_code == status_code, response
            if status_code == 400:
                assert message in response.json()[key][0]
        assert len(self._member.active_courses.all()) == init_active
        assert len(self._member.cancelled_courses.all()) == init_cancelled
