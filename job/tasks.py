import requests.exceptions
from celery_singleton import Singleton
from django.utils import timezone
from linkedin_api.linkedin import default_evade

from job import JobStatus
from job.models import JobLocation, JobTitle, Job
from linkedin.models import LinkedinAccount
from relohub import celery_app as app


@app.task(
    base=Singleton,
    name="job.search_jobs",
    autoretry_for=(Exception,),
    max_retries=3,
    time_limit=60 * 30,
    lock_expiry=60 * 30,
)
def search_jobs():
    linkedin_account: LinkedinAccount = (
        LinkedinAccount.objects.filter(is_active=True).order_by("last_used").first()
    )
    linkedin_account.last_used = timezone.now()
    linkedin_account.save()

    client = linkedin_account.client

    locations = JobLocation.objects.filter(is_active=True).all()
    job_titles = JobTitle.objects.filter(is_active=True).all()

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
