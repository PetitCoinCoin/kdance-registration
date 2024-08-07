"""Tests related to utilities functions."""
import pytest

from rest_framework import serializers

from accounts.api.serializers import validate_phone, validate_pwd


@pytest.mark.parametrize(
    "pwd",
    [
        "tropcourt",
        "pasdemajuscule",
        "PASDEMINUSCULE",
        "PasDeChiffre",
        "PasDeChiffre",
        "01234567899876543210",
        "AZERTY098765",
        "aZ0",
        "Az0!"
    ],
)
def test_validate_pwd_error(pwd):
    with pytest.raises(serializers.ValidationError):
        validate_pwd(pwd)


def test_validate_pwd():
    validate_pwd("SuperM0tdePass3")


@pytest.mark.parametrize(
    "phone",
    [
        "0123",
        "o12345679",
        "o123",
        "PasDeChiffre",
        "+33123456789",
    ],
)
def test_validate_phone_error(phone):
    with pytest.raises(serializers.ValidationError):
        validate_phone(phone)


def test_validate_phone():
    validate_phone("0123456789")
