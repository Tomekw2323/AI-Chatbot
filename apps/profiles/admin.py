from django.contrib import admin

from .models import SpecialistProfile


@admin.register(SpecialistProfile)
class SpecialistProfileAdmin(admin.ModelAdmin[SpecialistProfile]):
    list_display = (
        "__str__",
        "profession",
        "city",
        "open_to_work",
        "is_public",
        "is_blocked",
        "updated_at",
    )
    list_filter = ("profession", "open_to_work", "is_public", "is_blocked", "city__voivodeship")
    list_editable = ("is_blocked",)
    search_fields = ("user__email", "user__first_name", "user__last_name", "headline")
    autocomplete_fields = ("user", "city")
    filter_horizontal = ("specializations", "approaches")
    list_select_related = ("user", "city")
