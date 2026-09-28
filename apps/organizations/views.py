from typing import Any

from allauth.account.decorators import verified_email_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, UpdateView

from apps.accounts.services import require_user
from apps.core.ratelimit import ratelimit

from .forms import OrganizationForm
from .models import Organization
from .services import can_manage_organization, create_organization


class OrganizationDetailView(DetailView[Organization]):
    template_name = "organizations/organization_detail.html"
    context_object_name = "organization"

    def get_queryset(self) -> QuerySet[Organization]:
        return Organization.objects.public().select_related("city__voivodeship")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["can_manage"] = can_manage_organization(self.request.user, self.object)
        return context


@method_decorator([verified_email_required, ratelimit("organization_create")], name="dispatch")
class OrganizationCreateView(CreateView[Organization, OrganizationForm]):
    form_class = OrganizationForm
    template_name = "organizations/organization_form.html"

    def form_valid(self, form: OrganizationForm) -> HttpResponse:
        owner = require_user(self.request)
        self.object = create_organization(form.save(commit=False), owner=owner)
        messages.success(self.request, _("Organizacja została utworzona."))
        return HttpResponseRedirect(self.object.get_absolute_url())


@method_decorator(verified_email_required, name="dispatch")
class OrganizationUpdateView(UpdateView[Organization, OrganizationForm]):
    form_class = OrganizationForm
    template_name = "organizations/organization_form.html"
    queryset = Organization.objects.all()

    def get_object(self, queryset: QuerySet[Organization] | None = None) -> Organization:
        organization = super().get_object(queryset)
        if not can_manage_organization(self.request.user, organization):
            raise PermissionDenied
        return organization

    def form_valid(self, form: OrganizationForm) -> HttpResponse:
        messages.success(self.request, _("Zmiany zostały zapisane."))
        return super().form_valid(form)
