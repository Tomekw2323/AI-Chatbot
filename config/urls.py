from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpRequest, HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView

from apps.listings import views as listing_views

from .sitemaps import sitemaps


def healthz(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("", listing_views.home, name="home"),
    path("panel/", listing_views.dashboard, name="dashboard"),
    path("ogloszenia/", include("apps.listings.urls")),
    path("specjalisci/", include("apps.profiles.urls")),
    path("organizacje/", include("apps.organizations.urls")),
    path("konto/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("healthz/", healthz, name="healthz"),
]

admin.site.site_header = "BartoszUP – administracja"
admin.site.site_title = "BartoszUP"
