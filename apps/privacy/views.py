import json

from allauth.account.decorators import reauthentication_required
from django import forms
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from apps.accounts.services import require_user
from apps.core.ratelimit import ratelimit

from .services import AccountDeletionBlockedError, delete_account, export_user_data


class DeleteAccountForm(forms.Form):
    confirm_email = forms.EmailField(
        label=gettext_lazy("Wpisz swój adres e-mail, aby potwierdzić"),
    )

    def __init__(self, *args: object, email: str, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.email = email

    def clean_confirm_email(self) -> str:
        value = str(self.cleaned_data["confirm_email"])
        if value.lower() != self.email.lower():
            raise forms.ValidationError(_("Adres e-mail nie zgadza się z adresem konta."))
        return value


@login_required
def my_data(request: HttpRequest) -> HttpResponse:
    user = require_user(request)
    form = DeleteAccountForm(email=user.email)
    return render(request, "privacy/my_data.html", {"form": form})


@require_POST
@login_required
@reauthentication_required
@ratelimit("data_export")
def export_data(request: HttpRequest) -> HttpResponse:
    user = require_user(request)
    payload = json.dumps(export_user_data(user), ensure_ascii=False, indent=2)
    response = HttpResponse(payload, content_type="application/json; charset=utf-8")
    filename = f"bartoszup-dane-{timezone.now():%Y%m%d}.json"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "no-store"
    return response


@require_POST
@login_required
@reauthentication_required
def delete_account_view(request: HttpRequest) -> HttpResponse:
    user = require_user(request)
    form = DeleteAccountForm(request.POST, email=user.email)
    if not form.is_valid():
        return render(request, "privacy/my_data.html", {"form": form}, status=400)
    try:
        delete_account(user)
    except AccountDeletionBlockedError as exc:
        messages.error(
            request,
            _(
                "Nie można usunąć konta: jesteś jedynym właścicielem organizacji z innymi "
                "członkami (%(names)s). Nadaj rolę administratora innej osobie lub napisz do nas."
            )
            % {"names": str(exc)},
        )
        return redirect("privacy:my_data")
    logout(request)
    messages.success(request, _("Twoje konto i dane zostały usunięte."))
    return redirect("home")


def terms(request: HttpRequest) -> HttpResponse:
    return render(request, "privacy/terms.html")


def privacy_policy(request: HttpRequest) -> HttpResponse:
    return render(request, "privacy/privacy_policy.html")
