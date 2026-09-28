from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet
from django.urls import reverse

from apps.core.models import City
from apps.listings.models import Listing
from apps.organizations.models import Organization
from apps.profiles.models import SpecialistProfile


class ListingSitemap(Sitemap[Listing]):
    changefreq = "daily"

    def items(self) -> QuerySet[Listing]:
        return Listing.objects.public()

    def lastmod(self, obj: Listing):  # type: ignore[no-untyped-def]
        return obj.updated_at


class ProfileSitemap(Sitemap[SpecialistProfile]):
    changefreq = "weekly"

    def items(self) -> QuerySet[SpecialistProfile]:
        return SpecialistProfile.objects.public()

    def lastmod(self, obj: SpecialistProfile):  # type: ignore[no-untyped-def]
        return obj.updated_at


class OrganizationSitemap(Sitemap[Organization]):
    changefreq = "weekly"

    def items(self) -> QuerySet[Organization]:
        return Organization.objects.public()


class KindCitySitemap(Sitemap[tuple[str, str]]):
    """SEO landing pages such as /ogloszenia/gabinety/wroclaw/."""

    changefreq = "daily"

    def items(self) -> list[tuple[str, str]]:
        cities = City.objects.filter(is_featured=True).values_list("slug", flat=True)
        return [(kind, city) for kind in Listing.KIND_URL_SLUGS.values() for city in cities]

    def location(self, item: tuple[str, str]) -> str:
        return reverse(
            "listings:list_by_kind_city", kwargs={"kind_slug": item[0], "city_slug": item[1]}
        )


sitemaps = {
    "listings": ListingSitemap,
    "profiles": ProfileSitemap,
    "organizations": OrganizationSitemap,
    "landing": KindCitySitemap,
}
