from django.contrib import admin

from .models import Membership, Organization


class MembershipInline(admin.TabularInline[Membership, Organization]):
    model = Membership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin[Organization]):
    list_display = ("name", "kind", "city", "is_public", "is_verified", "is_blocked", "created_at")
    list_filter = ("kind", "is_verified", "is_blocked", "city__voivodeship")
    list_editable = ("is_verified", "is_blocked")
    search_fields = ("name", "tax_id", "contact_email")
    autocomplete_fields = ("city",)
    inlines = (MembershipInline,)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin[Membership]):
    list_display = ("user", "organization", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "organization__name")
    autocomplete_fields = ("user", "organization")
