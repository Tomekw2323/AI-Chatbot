from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.accounts.services import require_user
from apps.core.models import City
from apps.organizations.services import managed_organizations
from apps.profiles.models import SpecialistProfile

from .filters import ListingFilter
from .forms import AvailabilityFormSet, InquiryForm, ListingForm
from .models import InvalidTransitionError, Listing
from .permissions import can_edit_listing, can_send_inquiry, can_view_listing
from .services import send_inquiry

KIND_BY_URL_SLUG = {slug: kind for kind, slug in Listing.KIND_URL_SLUGS.items()}


def home(request: HttpRequest) -> HttpResponse:
    public = Listing.objects.public()
    counts = {
        row["kind"]: row["n"] for row in public.order_by().values("kind").annotate(n=Count("id"))
    }
    kinds = [
        {
            "value": value,
            "label": label,
            "slug": Listing.KIND_URL_SLUGS[value],
            "count": counts.get(value, 0),
        }
        for value, label in Listing.Kind.choices
    ]
    context = {
        "kinds": kinds,
        "latest": public.select_related("city", "organization")[:6],
        "featured_cities": City.objects.filter(is_featured=True),
        "filter": ListingFilter(queryset=Listing.objects.none()),
    }
    return render(request, "home.html", context)


def listing_list(
    request: HttpRequest, kind_slug: str | None = None, city_slug: str | None = None
) -> HttpResponse:
    """Filterable list. ``/ogloszenia/<kind>/<city>/`` are SEO aliases of query params."""
    data = request.GET.copy()
    kind: str | None = None
    city: City | None = None
    if kind_slug is not None:
        kind = KIND_BY_URL_SLUG.get(kind_slug)
        if kind is None:
            raise Http404
        data["kind"] = kind
    if city_slug is not None:
        city = get_object_or_404(City, slug=city_slug)
        data["city"] = city.slug

    queryset = (
        Listing.objects.public()
        .select_related("city", "organization")
        .prefetch_related("specializations")
    )
    filterset = ListingFilter(data, queryset=queryset)
    page = Paginator(filterset.qs, settings.LISTINGS_PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "filter": filterset,
        "page_obj": page,
        "seo_kind_label": Listing.Kind(kind).label if kind else None,
        "seo_city": city,
    }
    template = (
        "listings/_listing_results.html"
        if getattr(request, "htmx", False)
        else "listings/listing_list.html"
    )
    return render(request, template, context)


def listing_detail(request: HttpRequest, pk: int, slug: str) -> HttpResponse:
    listing = get_object_or_404(
        Listing.objects.select_related(
            "city__voivodeship", "organization", "author"
        ).prefetch_related("specializations", "availability_blocks"),
        pk=pk,
    )
    if not can_view_listing(request.user, listing):
        raise Http404
    if slug != listing.slug:
        return redirect(listing, permanent=True)
    author_profile = (
        SpecialistProfile.objects.public().filter(user_id=listing.author_id).first()
        if listing.organization is None
        else None
    )
    context = {
        "listing": listing,
        "can_edit": can_edit_listing(request.user, listing),
        "can_send_inquiry": can_send_inquiry(request.user, listing),
        "inquiry_form": InquiryForm(),
        "author_profile": author_profile,
    }
    return render(request, "listings/listing_detail.html", context)


def _save_listing_form(request: HttpRequest, listing: Listing | None) -> HttpResponse:
    user = require_user(request)
    instance = listing or Listing(author=user)
    if request.method == "POST":
        form = ListingForm(request.POST, instance=instance, user=user)
        formset = AvailabilityFormSet(request.POST, instance=instance, prefix="availability")
        is_room = request.POST.get("kind") == Listing.Kind.ROOM_RENTAL
        if form.is_valid() and (not is_room or formset.is_valid()):
            with transaction.atomic():
                saved = form.save(commit=False)
                wants_publish = request.POST.get("action") == "publish"
                if wants_publish and saved.can_transition_to(Listing.Status.PUBLISHED):
                    saved.publish()
                saved.save()
                form.save_m2m()
                if is_room:
                    formset.instance = saved
                    formset.save()
                else:
                    saved.availability_blocks.all().delete()
            messages.success(
                request,
                _("Ogłoszenie zostało opublikowane.")
                if saved.status == Listing.Status.PUBLISHED
                else _("Ogłoszenie zostało zapisane."),
            )
            return redirect(saved)
    else:
        form = ListingForm(instance=instance, user=user)
        formset = AvailabilityFormSet(instance=instance, prefix="availability")
    return render(
        request,
        "listings/listing_form.html",
        {"form": form, "formset": formset, "listing": listing},
    )


@login_required
def listing_create(request: HttpRequest) -> HttpResponse:
    return _save_listing_form(request, None)


@login_required
def listing_update(request: HttpRequest, pk: int) -> HttpResponse:
    listing = get_object_or_404(Listing, pk=pk)
    if not can_edit_listing(request.user, listing):
        raise PermissionDenied
    return _save_listing_form(request, listing)


@login_required
@require_POST
def listing_transition(request: HttpRequest, pk: int, action: str) -> HttpResponse:
    listing = get_object_or_404(Listing, pk=pk)
    if not can_edit_listing(request.user, listing):
        raise PermissionDenied
    actions = {"publish": listing.publish, "archive": listing.archive}
    if action not in actions:
        raise Http404
    try:
        actions[action]()
    except InvalidTransitionError:
        messages.error(request, _("Tej operacji nie można wykonać dla ogłoszenia w tym statusie."))
    else:
        listing.save()
        messages.success(
            request, _("Status ogłoszenia: %(status)s.") % {"status": listing.get_status_display()}
        )
    return redirect(request.POST.get("next") or "dashboard")


@login_required
@require_POST
def inquiry_create(request: HttpRequest, pk: int) -> HttpResponse:
    listing = get_object_or_404(Listing.objects.select_related("author"), pk=pk)
    if not can_send_inquiry(request.user, listing):
        raise PermissionDenied
    form = InquiryForm(request.POST)
    if form.is_valid():
        send_inquiry(listing, require_user(request), form.cleaned_data["message"])
        messages.success(request, _("Wiadomość została wysłana do autora ogłoszenia."))
        return redirect(listing)
    messages.error(request, _("Wiadomość nie może być pusta."))
    return redirect(listing)


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    user = require_user(request)
    organizations = managed_organizations(user)
    listings = (
        Listing.objects.filter(Q(author=user) | Q(organization__in=organizations))
        .select_related("city", "organization")
        .distinct()
        .order_by("-updated_at")
    )
    context: dict[str, Any] = {
        "profile": SpecialistProfile.objects.filter(user=user).first(),
        "organizations": organizations,
        "listings": listings,
    }
    return render(request, "listings/dashboard.html", context)
