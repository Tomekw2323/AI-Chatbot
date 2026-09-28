from typing import Any

import factory
from allauth.account.models import EmailAddress

from apps.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory[User]):
    """A user with a verified primary email; pass ``verified=False`` for an unverified one."""

    class Meta:
        model = User
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Jan"
    last_name = factory.Sequence(lambda n: f"Testowy{n}")
    password = factory.django.Password("password")

    @factory.post_generation
    def verified(self, create: bool, extracted: Any, **kwargs: Any) -> None:
        if create:
            EmailAddress.objects.get_or_create(
                user=self,
                email=self.email,
                defaults={"primary": True, "verified": extracted is not False},
            )
