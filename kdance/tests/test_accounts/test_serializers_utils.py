"""Tests related to utilities functions."""
import pytest

from rest_framework import serializers

from accounts.api.serializers import validate_phone, validate_pwd


def test_validate_pwd_error():
    for pwd in ( "tropcourt", "pasdemajuscule", "PASDEMINUSCULE", "PasDeChiffre", "01234567899876543210", "AZERTY098765", "aZ0", "Az0!"):
        with pytest.raises(serializers.ValidationError):
            print(pwd)
            validate_pwd(pwd)


def test_validate_pwd():
    validate_pwd("SuperM0tdePass3")


def test_validate_phone_error():
    for phone in ("0123", "o12345679", "o123", "PasDeChiffre", "+33123456789"):
        with pytest.raises(serializers.ValidationError):
            validate_phone(phone)


def test_validate_phone():
    validate_phone("0123456789")
