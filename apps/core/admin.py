from django.contrib import admin

from .models import City, Specialization, TherapyApproach, Voivodeship


@admin.register(Voivodeship)
class VoivodeshipAdmin(admin.ModelAdmin[Voivodeship]):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(City)
class CityAdmin(admin.ModelAdmin[City]):
    list_display = ("name", "voivodeship", "is_featured")
    list_filter = ("voivodeship", "is_featured")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Specialization, TherapyApproach)
class ReferenceAdmin(admin.ModelAdmin[Specialization | TherapyApproach]):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
