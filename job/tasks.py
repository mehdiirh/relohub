from time import sleep

import requests.exceptions
from celery_singleton import Singleton
from celery_singleton.exceptions import DuplicateTaskError
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from linkedin_api.linkedin import default_evade

from job import JobStatus
from job.models import JobLocation, JobTitle, Job, Company, JobSkill
from linkedin.models import LinkedinAccount
from relohub import celery_app as app


def get_least_used_account() -> LinkedinAccount:
    linkedin_account: LinkedinAccount = (
        LinkedinAccount.objects.filter(is_active=True).order_by("last_used").first()
    )
    linkedin_account.last_used = timezone.now()
    linkedin_account.save()

    return linkedin_account


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
    unique_on=["account_pk"],
    raise_on_duplicate=True,
    name="job.search_jobs",
    time_limit=6 * 60,
    lock_expiry=6 * 60,
)
def search_jobs(account_pk: int, location_pk: int, job_title_pk: int):
    account = LinkedinAccount.objects.get(pk=account_pk)
    location = JobLocation.objects.get(pk=location_pk)
    job_title = JobTitle.objects.get(pk=job_title_pk)

    client = account.client

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
        except requests.exceptions.JSONDecodeError as e:
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
    name="job.run_search_jobs",
    lock_expiry=60 * 60,
)
def run_search_jobs():
    locations = JobLocation.objects.filter(is_active=True).all()
    job_titles = JobTitle.objects.filter(is_active=True).all()

    pending_task_args = []
    for location in locations:
        for job_title in job_titles:
            account = get_least_used_account()
            args = (account.pk, location.pk, job_title.pk)

            try:
                search_jobs.delay(*args)
            except DuplicateTaskError:
                pending_task_args.append(args)

    while pending_task_args:
        for idx, args in enumerate(pending_task_args):
            try:
                search_jobs.delay(*args)
                pending_task_args.pop(idx)
            except DuplicateTaskError:
                pass

        sleep(5)


@app.task(
    base=Singleton,
    unique_on=["account_pk"],
    raise_on_duplicate=True,
    name="job.process_jobs",
    time_limit=3 * 60,
    lock_expiry=3 * 60,
)
def process_jobs(account_pk: int, job_pks: list[int]):
    account = LinkedinAccount.objects.get(pk=account_pk)
    jobs = Job.objects.filter(pk__in=job_pks).all()

    client = account.client

    for job in jobs:
        while True:
            try:
                job_data = client.get_job(job.linkedin_id)
                break
            except requests.exceptions.JSONDecodeError:
                default_evade()
                continue

        # noinspection PyUnboundLocalVariable
        if job_data["jobState"] != "LISTED":
            job.status = JobStatus.EXPIRED
            job.save()
            continue

        try:
            # noinspection PyUnboundLocalVariable
            job.company = resolve_company(job_data)
        except KeyError:
            job.delete()
            continue

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

        while True:
            try:
                job_skills = client.get_job_skills(job.linkedin_id)
                break
            except requests.exceptions.JSONDecodeError:
                default_evade()
                continue

        # noinspection PyUnboundLocalVariable
        for skill_data in job_skills["skillMatchStatuses"]:
            skill = skill_data["skill"]
            name = skill["name"]
            linkedin_id = skill["entityUrn"].split(":")[-1]

            skill_object, skill_created = JobSkill.objects.get_or_create(
                linkedin_id=linkedin_id,
                defaults={"name": name},
            )
            job.job_skills.add(skill_object)

        # key in description: 1 points
        # key in title: 2 points
        # key+complement in description: 3 points
        # key+title in description: 5 points
        job_contains_keywords = False
        points = 0
        for key in settings.LINKEDIN_JOB_DESCRIPTION_KEYWORDS:
            if key.lower() in job.description.lower():
                job_contains_keywords = True
                points += 1

            if key.lower() in job.title.lower():
                job_contains_keywords = True
                points += 2

        if job_contains_keywords:
            for key_complement in settings.LINKEDIN_JOB_DESCRIPTION_KEYWORD_COMPLEMENTS:
                if key_complement.lower() in job.description.lower():
                    points += 3

                if key_complement.lower() in job.title.lower():
                    points += 5

        job.points = points

        if points > 0:
            job.status = JobStatus.WAITING_FOR_REVIEW
        else:
            job.status = JobStatus.REJECTED

        job.save()
        default_evade()


@app.task(
    base=Singleton,
    name="job.run_process_jobs",
    lock_expiry=60 * 60,
)
def run_process_jobs():
    jobs = (
        Job.objects.filter(is_active=True, status=JobStatus.PARTIALLY_PROCEEDED)
        .order_by("created_at")
        .values_list("pk", flat=True)
        .distinct()
    )

    chunk = 10
    pending_task_args = []
    for offset in range(0, len(jobs), chunk):
        sliced_jobs = jobs[offset : offset + chunk]

        account = get_least_used_account()
        args = (account.pk, sliced_jobs)

        try:
            process_jobs.delay(*args)
        except DuplicateTaskError:
            pending_task_args.append(args)

    while pending_task_args:
        for idx, args in enumerate(pending_task_args):
            try:
                process_jobs.delay(*args)
                pending_task_args.pop(idx)
            except DuplicateTaskError:
                pass

        sleep(5)
