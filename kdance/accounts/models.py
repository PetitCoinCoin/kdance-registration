"""
Copyright 2024, 2025 Andréa Marnier

This file is part of KDance registration.

KDance registration is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by the
Free Software Foundation, either version 3 of the License, or any later version.

KDance registration is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
for more details.

You should have received a copy of the GNU Affero General Public License along
with KDance registration. If not, see <https://www.gnu.org/licenses/>.
"""

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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
    phone = models.CharField(
        blank=False,
        null=False,
        validators=[RegexValidator(r"\d{10}")],
        max_length=10,
    )

    @property
    def full_address(self) -> str:
        return f"{self.address}, {self.postal_code} {self.city}"


class ResetPassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    request_hash = models.CharField(null=False, blank=False, max_length=128)
    created = models.DateTimeField(auto_now=True)
