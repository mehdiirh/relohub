from django.contrib import admin

from core.admin import BaseModelAdmin
from job.models import Job, JobLocation, JobTitle, Company  # noqa


@admin.register(Company)
class CompanyAdmin(BaseModelAdmin):
    list_display = ["name", "universal_name", "linkedin_id"]


@admin.register(JobTitle)
class JobTitleAdmin(BaseModelAdmin):
    list_display = ["title", "linkedin_id"]


@admin.register(JobLocation)
class JobLocationAdmin(BaseModelAdmin):
    list_display = ["title", "linkedin_geo_id", "flag_emoji"]


@admin.register(Job)
class JobAdmin(BaseModelAdmin):
    list_display = ["id", "title", "company", "full_location", "status"]
