import requests.exceptions
from celery_singleton import Singleton
from django.core.files.base import ContentFile
from django.utils import timezone
from linkedin_api.linkedin import default_evade, Linkedin

from job import JobStatus
from job.models import JobLocation, JobTitle, Job, Company
from linkedin.models import LinkedinAccount
from relohub import celery_app as app


def get_client() -> Linkedin:
    linkedin_account: LinkedinAccount = (
        LinkedinAccount.objects.filter(is_active=True).order_by("last_used").first()
    )
    linkedin_account.last_used = timezone.now()
    linkedin_account.save()

    return linkedin_account.client


def resolve_company(job_data: dict):
    company_data = job_data["companyDetails"][
        "com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany"
    ]["companyResolutionResult"]

    company, created = Company.objects.get_or_create(
        linkedin_id=company_data["entityUrn"].split(":")[-1],
        defaults={
            "name": company_data["name"],
            "universal_name": company_data["universalName"],
        },
    )
    if not company.logo:
        if (
            logo := company_data.get("logo", {})
            .get("image", {})
            .get("com.linkedin.common.VectorImage", {})
        ):
            biggest_size = list(sorted(logo["artifacts"], key=lambda x: x["width"]))[-1]
            url = logo["rootUrl"] + biggest_size["fileIdentifyingUrlPathSegment"]
            result = requests.get(url)
            if result.ok:
                company.logo.save(
                    company.universal_name + ".png", ContentFile(result.content)
                )
                company.save()

    return company


@app.task(
    base=Singleton,
    name="job.search_jobs",
    autoretry_for=(Exception,),
    max_retries=3,
    time_limit=60 * 30,
    lock_expiry=60 * 30,
)
def search_jobs():
    locations = JobLocation.objects.filter(is_active=True).all()
    job_titles = JobTitle.objects.filter(is_active=True).all()

    client = get_client()

    for location in locations:
        for job_title in job_titles:
            jobs = []
            limit, chunk, offset = 200, 20, 0
            while True:
                try:
                    new_jobs = client.search_jobs(
                        location_geo_id=location.linkedin_geo_id,
                        job_title=[job_title.linkedin_id],
                        offset=offset,
                        listed_at=24 * 60 * 60,
                        limit=chunk,
                    )
                except requests.exceptions.JSONDecodeError:
                    default_evade()
                    continue

                jobs.extend(new_jobs)
                offset += chunk

                if any(
                    [
                        not new_jobs,
                        offset >= limit,
                        len(new_jobs) < chunk,
                    ]
                ):
                    break

                default_evade()

            for _job in jobs:
                job_id = _job["trackingUrn"].split(":")[-1]
                title = _job["title"]

                job, job_created = Job.objects.get_or_create(
                    linkedin_id=job_id,
                    defaults={
                        "title": title,
                        "status": JobStatus.PARTIALLY_PROCEEDED,
                        "location": location,
                    },
                )
                job.job_titles.add(job_title)
                job.save()


@app.task(
    base=Singleton,
    name="job.process_jobs",
    autoretry_for=(Exception,),
    max_retries=3,
    time_limit=60 * 20,
    lock_expiry=60 * 20,
)
def process_jobs():
    jobs = Job.objects.filter(is_active=True, status=JobStatus.PARTIALLY_PROCEEDED)[:20]

    client = get_client()

    for job in jobs:
        while True:
            try:
                job_data = client.get_job(job.linkedin_id)
                break
            except requests.exceptions.JSONDecodeError:
                default_evade()
                continue

        # noinspection PyUnboundLocalVariable
        job.company = resolve_company(job_data)
        job.description = job_data["description"]["text"]
        job.attributes = job_data["description"]["attributes"]
        job.remote = job_data["workRemoteAllowed"]
        job.full_location = job_data["formattedLocation"]
        job.listed_at = job_data["listedAt"]

        for workplace_type in job_data["workplaceTypes"]:
            workplace_type = workplace_type.split(":")[-1]
            if workplace_type == "1":
                job.on_site = True
            if workplace_type == "2":
                job.remote = True
            if workplace_type == "3":
                job.hybrid = True

        job.status = JobStatus.FULLY_PROCEEDED
        job.save()

        default_evade()
