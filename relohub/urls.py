from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from linkedin.views import add_job_titles

urlpatterns = [
    path("add_job_titles/", add_job_titles, name="add-job-title"),
    path("admin/", admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.MEDIA_ROOT)
