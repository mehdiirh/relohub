from django.contrib import admin

from core.admin import BaseModelAdmin
from core.utils import remove_exponent_decorator
from job.models import Job, JobLocation, JobTitle, Company, JobSkill  # noqa


@admin.register(Company)
class CompanyAdmin(BaseModelAdmin):
    list_display = ["name", "universal_name", "linkedin_id", "jobs_count"]
    search_fields = ["name", "universal_name"]

    @remove_exponent_decorator
    def jobs_count(self, obj):
        return obj.jobs.count()


@admin.register(JobTitle)
class JobTitleAdmin(BaseModelAdmin):
    list_display = ["title", "linkedin_id", "jobs_count", "is_active"]
    search_fields = ["title", "children__title", "other_names__icontains"]

    @remove_exponent_decorator
    def jobs_count(self, obj):
        return obj.jobs.count()


@admin.register(JobSkill)
class JobSkillAdmin(BaseModelAdmin):
    list_display = ["name", "linkedin_id", "jobs_count"]
    search_fields = ["name", "linkedin_id"]

    @remove_exponent_decorator
    def jobs_count(self, obj):
        return obj.jobs.count()


@admin.register(JobLocation)
class JobLocationAdmin(BaseModelAdmin):
    list_display = ["title", "linkedin_geo_id", "flag_emoji", "jobs_count", "is_active"]
    search_fields = [
        "title",
        "iso_code",
        "linkedin_geo_id",
        "flag_emoji",
    ]

    @remove_exponent_decorator
    def jobs_count(self, obj):
        return obj.jobs.count()


@admin.register(Job)
class JobAdmin(BaseModelAdmin):
    list_display = ["id", "title", "company", "location", "full_location", "status"]
    list_filter = ["status", "location", "job_titles"]
    search_fields = [
        "title__icontains",
        "description__icontains",
        "company__name",
        "company__universal_name",
    ]
    autocomplete_fields = ["job_skills", "job_titles", "location"]
