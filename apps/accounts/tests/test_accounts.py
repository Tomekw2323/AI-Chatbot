import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.services import has_verified_email, require_user

from .factories import UserFactory

pytestmark = pytest.mark.django_db

SIGNUP = {
    "email": "nowa@example.com",
    "first_name": "Ewa",
    "last_name": "Zielińska",
    "password1": "Bardzo-trudne-haslo-42",
    "password2": "Bardzo-trudne-haslo-42",
}


def test_create_user_uses_email_as_username() -> None:
    user = User.objects.create_user(email="Anna@Example.com", password="secret-pass-123")
    assert user.email == "Anna@example.com"
    assert user.check_password("secret-pass-123")
    assert not user.is_staff


def test_create_user_requires_email() -> None:
    with pytest.raises(ValueError, match="Email"):
        User.objects.create_user(email="", password="x")


def test_create_superuser() -> None:
    admin = User.objects.create_superuser(email="admin@example.com", password="x")
    assert admin.is_staff and admin.is_superuser


def test_str_prefers_full_name() -> None:
    user = User(email="a@example.com", first_name="Anna", last_name="Nowak")
    assert str(user) == "Anna Nowak"
    assert str(User(email="b@example.com")) == "b@example.com"


def test_signup_requires_accepting_terms(client) -> None:
    response = client.post(reverse("account_signup"), SIGNUP)
    assert response.status_code == 200
    assert "accept_terms" in response.context["form"].errors
    assert not User.objects.exists()


def test_signup_stores_names_and_consent_time(client) -> None:
    response = client.post(reverse("account_signup"), {**SIGNUP, "accept_terms": "on"})
    assert response.status_code == 302
    user = User.objects.get(email="nowa@example.com")
    assert (user.first_name, user.last_name) == ("Ewa", "Zielińska")
    assert user.terms_accepted_at is not None


def test_signup_rejects_weak_password(client) -> None:
    data = {**SIGNUP, "accept_terms": "on", "password1": "haslo123", "password2": "haslo123"}
    response = client.post(reverse("account_signup"), data)
    assert response.status_code == 200
    assert not User.objects.exists()


def test_signup_page_links_legal_documents(client) -> None:
    content = client.get(reverse("account_signup")).content.decode()
    assert reverse("privacy:terms") in content
    assert reverse("privacy:policy") in content


def test_has_verified_email() -> None:
    assert has_verified_email(UserFactory.create())
    assert not has_verified_email(UserFactory.create(verified=False))
    assert not has_verified_email(AnonymousUser())


def test_require_user_denies_anonymous() -> None:
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    with pytest.raises(PermissionDenied):
        require_user(request)


def test_failed_logins_are_rate_limited(client, settings) -> None:
    settings.ACCOUNT_RATE_LIMITS = {"login_failed": "3/m/ip"}
    UserFactory.create(email="ofiara@example.com")
    data = {"login": "ofiara@example.com", "password": "zle-haslo"}
    for _ in range(3):
        client.post(reverse("account_login"), data)
    # Even the correct password is refused while throttled.
    correct = {"login": "ofiara@example.com", "password": "password"}
    response = client.post(reverse("account_login"), correct)
    assert "Zbyt wiele nieudanych prób logowania" in response.content.decode()
    assert "_auth_user_id" not in client.session


def test_signup_is_rate_limited(client, settings) -> None:
    settings.ACCOUNT_RATE_LIMITS = {"signup": "1/m/ip"}
    client.post(reverse("account_signup"), {**SIGNUP, "accept_terms": "on"})
    client.logout()
    second = {**SIGNUP, "email": "druga@example.com", "accept_terms": "on"}
    assert client.post(reverse("account_signup"), second).status_code == 429
