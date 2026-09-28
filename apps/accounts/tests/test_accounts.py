import pytest
from django.urls import reverse

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_create_user_uses_email_as_username() -> None:
    user = User.objects.create_user(email="Anna@Example.com", password="secret-pass-123")
    assert user.email == "Anna@example.com"
    assert user.check_password("secret-pass-123")
    assert not user.is_staff


def test_create_superuser() -> None:
    admin = User.objects.create_superuser(email="admin@example.com", password="x")
    assert admin.is_staff and admin.is_superuser


def test_str_prefers_full_name() -> None:
    user = User(email="a@example.com", first_name="Anna", last_name="Nowak")
    assert str(user) == "Anna Nowak"
    assert str(User(email="b@example.com")) == "b@example.com"


def test_signup_stores_first_and_last_name(client) -> None:
    response = client.post(
        reverse("account_signup"),
        {
            "email": "nowa@example.com",
            "first_name": "Ewa",
            "last_name": "Zielińska",
            "password1": "Bardzo-trudne-haslo-42",
            "password2": "Bardzo-trudne-haslo-42",
        },
    )
    assert response.status_code == 302
    user = User.objects.get(email="nowa@example.com")
    assert (user.first_name, user.last_name) == ("Ewa", "Zielińska")
