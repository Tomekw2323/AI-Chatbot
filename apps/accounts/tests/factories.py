import factory

from apps.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory[User]):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Jan"
    last_name = factory.Sequence(lambda n: f"Testowy{n}")
    password = factory.django.Password("password")
