"""Tests related to Teacher API view."""
import pytest

from django.urls import reverse
from parameterized import parameterized

from members.api.views import TeacherViewSet
from members.models import Teacher
from tests.authentication import AuthenticatedAction, AuthTestCase


@pytest.mark.django_db
class TestTeacherApiView(AuthTestCase):
    view_function = TeacherViewSet
    _kwargs = {}

    _teacher: Teacher | None = None

    @pytest.fixture(autouse=True)
    def set_teacher(self):
        teacher, _ = Teacher.objects.get_or_create(name="Globule")
        self._teacher = teacher

    @property
    def view_url(self):
        return reverse(
            f"api-teachers-{'detail' if 'pk' in self._kwargs else 'list'}",
            kwargs=self._kwargs,
        )

    @parameterized.expand([
        ("get", 200, 200, False),
        ("get", 200, 200, True),
        ("post", 403, 400, False),
        ("put", 403, 405, True),
        ("patch", 403, 200, True),
        ("delete", 403, 204, True),
    ])
    def test_permissions(self, method, user_status, superuser_status, with_pk):
        self._kwargs = {"pk": self._teacher.pk} if with_pk else {}
        assert self.users_have_permission(
            method=method,
            user_status=user_status,
            superuser_status=superuser_status,
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
        self._kwargs = {"pk": self._teacher.pk} if with_pk else {}
        assert self.anonymous_has_permission(method, 403)

    def test_get_list(self):
        self._kwargs = {}
        assert Teacher.objects.count() == 1
        last_teacher = Teacher.objects.create(name="Zohra")
        first_teacher = Teacher.objects.create(name="Alberto")
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 200, response
            response_json = response.json()
            assert len(response_json) == 3
            # test sorting (alphabetically)
            assert response_json[0]["id"] == first_teacher.pk
            assert response_json[-1]["id"] == last_teacher.pk

    def test_get_one(self):
        new_teacher = Teacher.objects.create(name="Chip")
        self._kwargs = {"pk": new_teacher.pk}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.get(self.view_url)
            assert response.status_code == 200, response
            response_json = response.json()
            assert response_json["id"] == new_teacher.pk
            assert response_json["name"] == new_teacher.name

    @parameterized.expand(["chIp", "Chip", "CHIP", "chip"])
    def test_post(self, name):
        self._kwargs = {}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(
                self.view_url,
                data={"name": name},
                content_type="application/json",
            )
            assert response.status_code == 201, response
            assert response.json()["name"] == "Chip"

    @parameterized.expand([
        ("Globule", "Un objet teacher avec ce champ name existe déjà."),
        ("gloBule", "Ce professeur existe déjà."),
    ])
    def test_post_payload_error(self, name, message):
        self._kwargs = {}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.post(
                self.view_url,
                data={"name": name},
                content_type="application/json",
            )
            assert response.status_code == 400, response
            assert message in response.json()["name"]

    def test_patch(self):
        new_teacher = Teacher.objects.create(name="Chip")
        new_name = "Ken-Patrick"
        self._kwargs = {"pk": new_teacher.pk}

        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(
                self.view_url,
                data={"name": new_name},
                content_type="application/json",
            )
            assert response.status_code == 200, response
            assert response.json()["name"] == new_name
        new_teacher.refresh_from_db()
        assert new_teacher.name == new_name

    def test_patch_payload_error(self):
        new_teacher = Teacher.objects.create(name="Chip")
        self._kwargs = {"pk": self._teacher.pk}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.patch(
                self.view_url,
                data={"name": new_teacher.name},
                content_type="application/json",
            )
            assert response.status_code == 400, response
            assert "Un objet teacher avec ce champ name existe déjà." in response.json()["name"]

    def test_delete(self):
        self._kwargs = {"pk": self._teacher.pk}
        with AuthenticatedAction(self.client, self.super_testuser):
            response = self.client.delete(self.view_url)
            assert response.status_code == 204, response
        assert Teacher.objects.count() == 0
