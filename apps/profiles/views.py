from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.generic import DetailView

from apps.accounts.forms import UserNameForm
from apps.accounts.services import require_user

from .filters import SpecialistProfileFilter
from .forms import SpecialistProfileForm
from .models import SpecialistProfile


def specialist_list(request: HttpRequest) -> HttpResponse:
    queryset = (
        SpecialistProfile.objects.public()
        .select_related("user", "city")
        .prefetch_related("specializations")
    )
    filterset = SpecialistProfileFilter(request.GET or None, queryset=queryset)
    page = Paginator(filterset.qs, settings.LISTINGS_PER_PAGE).get_page(request.GET.get("page"))
    context = {"filter": filterset, "page_obj": page}
    template = (
        "profiles/_specialist_results.html"
        if getattr(request, "htmx", False)
        else "profiles/specialist_list.html"
    )
    return render(request, template, context)


class SpecialistDetailView(DetailView[SpecialistProfile]):
    template_name = "profiles/specialist_detail.html"
    context_object_name = "profile"

    def get_queryset(self) -> QuerySet[SpecialistProfile]:
        return (
            SpecialistProfile.objects.public()
            .select_related("user", "city__voivodeship")
            .prefetch_related("specializations", "approaches")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["is_owner"] = self.object.user_id == self.request.user.pk
        return context


@login_required
def edit_own_profile(request: HttpRequest) -> HttpResponse:
    """Create or update the signed-in user's profile (one per user)."""
    user = require_user(request)
    profile = SpecialistProfile.objects.filter(user=user).first()
    if request.method == "POST":
        name_form = UserNameForm(request.POST, instance=user)
        form = SpecialistProfileForm(request.POST, instance=profile)
        if name_form.is_valid() and form.is_valid():
            name_form.save()
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            form.save_m2m()
            messages.success(request, _("Profil został zapisany."))
            return redirect("dashboard")
    else:
        name_form = UserNameForm(instance=user)
        form = SpecialistProfileForm(instance=profile)
    return render(
        request,
        "profiles/profile_form.html",
        {"form": form, "name_form": name_form, "profile": profile},
    )
