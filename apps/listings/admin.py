from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import Inquiry, Listing, RoomAvailabilityBlock


class RoomAvailabilityBlockInline(admin.TabularInline[RoomAvailabilityBlock, Listing]):
    model = RoomAvailabilityBlock
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin[Listing]):
    """Moderation happens here: flag (hide) or unflag listings, read inquiries."""

    list_display = (
        "title",
        "kind",
        "city",
        "organization",
        "author",
        "status",
        "is_flagged",
        "published_at",
        "expires_at",
    )
    list_filter = ("status", "kind", "is_flagged", "city__voivodeship")
    search_fields = ("title", "description", "author__email", "organization__name")
    autocomplete_fields = ("author", "organization", "city")
    filter_horizontal = ("specializations",)
    readonly_fields = ("created_at", "updated_at", "published_at")
    list_select_related = ("city", "organization", "author")
    inlines = (RoomAvailabilityBlockInline,)
    actions = ("flag_listings", "unflag_listings")
    date_hierarchy = "created_at"

    @admin.action(description=_("Ukryj zaznaczone (moderacja)"))
    def flag_listings(self, request: HttpRequest, queryset: QuerySet[Listing]) -> None:
        updated = queryset.update(is_flagged=True)
        self.message_user(request, _("Ukryto %(n)d ogłoszeń.") % {"n": updated}, messages.SUCCESS)

    @admin.action(description=_("Przywróć zaznaczone"))
    def unflag_listings(self, request: HttpRequest, queryset: QuerySet[Listing]) -> None:
        updated = queryset.update(is_flagged=False)
        self.message_user(
            request, _("Przywrócono %(n)d ogłoszeń.") % {"n": updated}, messages.SUCCESS
        )


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin[Inquiry]):
    list_display = ("listing", "sender_email", "recipient_email", "email_sent", "created_at")
    list_filter = ("email_sent",)
    search_fields = ("sender_email", "recipient_email", "listing__title")
    readonly_fields = [f.name for f in Inquiry._meta.fields]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
