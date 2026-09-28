"""Create demo users, organizations, profiles and listings for local development.

Idempotent: re-running it does not duplicate data. Never run in production.
"""

from datetime import time
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.core.models import City, Specialization, TherapyApproach
from apps.listings.models import Listing, RoomAvailabilityBlock
from apps.organizations.models import Membership, Organization
from apps.profiles.models import SpecialistProfile

DEMO_PASSWORD = "demo12345"  # noqa: S105


class Command(BaseCommand):
    help = "Seed demo data (users password: demo12345). Development only."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG:
            raise CommandError("seed_demo is only allowed with DEBUG=True.")
        if not City.objects.exists():
            call_command("loaddata", "reference_data")
        with transaction.atomic():
            self._seed()
        self.stdout.write(
            self.style.SUCCESS("Demo data ready. Log in as anna@example.com / demo12345")
        )

    def _user(self, email: str, first: str, last: str, **extra: Any) -> User:
        user, created = User.objects.get_or_create(
            email=email, defaults={"first_name": first, "last_name": last, **extra}
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user

    def _seed(self) -> None:
        wroclaw = City.objects.get(slug="wroclaw")
        warszawa = City.objects.get(slug="warszawa")
        krakow = City.objects.get(slug="krakow")
        spec = {s.slug: s for s in Specialization.objects.all()}
        approach = {a.slug: a for a in TherapyApproach.objects.all()}

        self._user("admin@example.com", "Admin", "BartoszUP", is_staff=True, is_superuser=True)
        anna = self._user("anna@example.com", "Anna", "Kowalska")
        piotr = self._user("piotr@example.com", "Piotr", "Nowak")
        ola = self._user("ola@example.com", "Aleksandra", "Wiśniewska")

        profile, _ = SpecialistProfile.objects.get_or_create(
            user=anna,
            defaults={
                "academic_title": "mgr",
                "profession": SpecialistProfile.Profession.PSYCHOTHERAPIST,
                "headline": "Psychoterapeutka CBT, pracuję z dorosłymi i parami.",
                "bio": "Certyfikowana psychoterapeutka CBT. 8 lat doświadczenia.",
                "city": wroclaw,
                "works_online": True,
                "contact_email": "anna@example.com",
            },
        )
        profile.specializations.set(
            [spec["psychoterapia-indywidualna-doroslych"], spec["psychoterapia-par"]]
        )
        profile.approaches.set([approach["poznawczo-behawioralny-cbt"]])

        student, _ = SpecialistProfile.objects.get_or_create(
            user=ola,
            defaults={
                "profession": SpecialistProfile.Profession.STUDENT,
                "headline": "Studentka V roku psychologii, szukam praktyk klinicznych.",
                "city": krakow,
                "open_to_work": True,
            },
        )
        student.specializations.set([spec["psychologia-kliniczna"]])

        clinic, created = Organization.objects.get_or_create(
            name="Centrum Psychologii Wrocław",
            defaults={
                "kind": Organization.Kind.CLINIC,
                "city": wroclaw,
                "address": "ul. Świdnicka 1, Wrocław",
                "description": "Poradnia psychologiczna i psychoterapeutyczna.",
                "contact_email": "kontakt@example.com",
                "is_verified": True,
            },
        )
        if created:
            Membership.objects.create(organization=clinic, user=piotr, role=Membership.Role.OWNER)
            Membership.objects.create(organization=clinic, user=anna, role=Membership.Role.MEMBER)

        ops, created = Organization.objects.get_or_create(
            name="Ośrodek Pomocy Społecznej – Mokotów",
            defaults={"kind": Organization.Kind.PUBLIC_INSTITUTION, "city": warszawa},
        )
        if created:
            Membership.objects.create(organization=ops, user=piotr, role=Membership.Role.ADMIN)

        if Listing.objects.exists():
            return

        def create(**fields: Any) -> Listing:
            specializations = fields.pop("specializations", [])
            listing = Listing(**fields)
            listing.publish()
            listing.save()
            listing.specializations.set(specializations)
            return listing

        create(
            kind=Listing.Kind.JOB,
            title="Psycholog dziecięcy – poradnia, 3/4 etatu",
            description="Szukamy psychologa do pracy z dziećmi i młodzieżą. Diagnoza i terapia.",
            author=piotr,
            organization=clinic,
            city=wroclaw,
            employment_type=Listing.EmploymentType.EMPLOYMENT_CONTRACT,
            work_mode=Listing.WorkMode.ON_SITE,
            salary_min=6500,
            salary_max=8500,
            salary_period=Listing.SalaryPeriod.MONTH,
            specializations=[spec["psychologia-dzieci-i-mlodziezy"]],
        )
        create(
            kind=Listing.Kind.JOB,
            title="Psycholog w zespole interdyscyplinarnym OPS",
            description="Ośrodek Pomocy Społecznej zatrudni psychologa (umowa o pracę).",
            author=piotr,
            organization=ops,
            city=warszawa,
            employment_type=Listing.EmploymentType.EMPLOYMENT_CONTRACT,
            work_mode=Listing.WorkMode.ON_SITE,
            specializations=[
                spec["pomoc-spoleczna-i-praca-srodowiskowa"],
                spec["interwencja-kryzysowa"],
            ],
        )
        create(
            kind=Listing.Kind.INTERNSHIP,
            title="Praktyki studenckie z psychologii klinicznej",
            description="Przyjmiemy 2 studentów IV–V roku na praktyki (120 h).",
            author=piotr,
            organization=clinic,
            city=wroclaw,
            employment_type=Listing.EmploymentType.UNPAID,
            specializations=[spec["psychologia-kliniczna"]],
        )
        create(
            kind=Listing.Kind.VOLUNTEERING,
            title="Wolontariat w telefonie zaufania",
            description="Dyżury 2× w miesiącu, szkolenie zapewniamy.",
            author=piotr,
            organization=ops,
            city=warszawa,
            work_mode=Listing.WorkMode.REMOTE,
            specializations=[spec["interwencja-kryzysowa"]],
        )
        create(
            kind=Listing.Kind.JOB_SEEKING,
            title="Studentka psychologii szuka praktyk – Kraków",
            description="Chętnie dołączę do zespołu poradni. Dostępna od października.",
            author=ola,
            city=krakow,
            work_mode=Listing.WorkMode.ON_SITE,
        )
        room = create(
            kind=Listing.Kind.ROOM_RENTAL,
            title="Gabinet terapeutyczny na godziny – centrum Wrocławia",
            description="Przytulny, wyciszony gabinet 14 m² w kamienicy, poczekalnia wspólna.",
            author=piotr,
            organization=clinic,
            city=wroclaw,
            address="Stare Miasto",
            price_amount=Decimal("45.00"),
            price_unit=Listing.PriceUnit.HOUR,
            room_area_m2=14,
            amenities="2 fotele, kozetka, klimatyzacja",
            availability_description="Poza blokami poniżej – do uzgodnienia.",
        )
        RoomAvailabilityBlock.objects.bulk_create(
            [
                RoomAvailabilityBlock(
                    listing=room, weekday=1, start_time=time(16), end_time=time(21)
                ),
                RoomAvailabilityBlock(
                    listing=room, weekday=3, start_time=time(16), end_time=time(21)
                ),
                RoomAvailabilityBlock(
                    listing=room, weekday=5, start_time=time(9), end_time=time(15)
                ),
            ]
        )
