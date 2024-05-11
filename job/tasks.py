import re
from time import sleep

import requests.exceptions
from celery_singleton import Singleton
from celery_singleton.exceptions import DuplicateTaskError
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from linkedin_api.linkedin import default_evade, get_id_from_urn

from core.exceptions import NoLinkedinAccountError, NotValidCompanyError
from job import JobStatus
from job.models import JobLocation, JobTitle, Job, Company, JobSkill
from linkedin.models import LinkedinAccount
from relohub import celery_app as app


def get_least_used_account() -> LinkedinAccount:
    """
    Get least used LinkedinAccount

    Raises:
        NoLinkedinAccountError: If there's no active LinkedinAccount available

    Returns:
        LinkedinAccount: The Least used Linkedin Account instance
    """

    linkedin_account: LinkedinAccount = (
        LinkedinAccount.objects.filter(is_active=True).order_by("last_used").first()
    )

    if not linkedin_account:
        raise NoLinkedinAccountError("No active LinkedinAccount available.")

    linkedin_account.last_used = timezone.now()
    linkedin_account.save()

    return linkedin_account


def resolve_company(job_data: dict) -> Company:
    """
    Resolve company of the job, save name, id, universal name and logo to the database

    Args:
        job_data: Job data fetched from Linkedin

    Returns:
        Company: created/updated company instance
    """

    company_data = job_data["company"]

    if company_data is None:
        raise NotValidCompanyError

    company, created = Company.objects.get_or_create(
        linkedin_id=get_id_from_urn(company_data["entityUrn"]),
        defaults={
            "name": company_data["name"],
        },
    )

    if not company.logo:
        if logo := company_data.get("logoResolutionResult", {}).get("vectorImage", {}):
            biggest_size = list(sorted(logo["artifacts"], key=lambda x: x["width"]))[-1]
            url = logo["rootUrl"] + biggest_size["fileIdentifyingUrlPathSegment"]

            universal_name = re.match(r"/\d/\d+/(.+)_logo\?", url)
            if universal_name:
                company.universal_name = universal_name.group(1).replace("_", "-")

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
    """
    Search jobs based on provided args

    Args:
        account_pk: LinkedinAccount primary-key
        location_pk: JobLocation primary-key
        job_title_pk: JobTitle primary-key
    """

    account = LinkedinAccount.objects.get(pk=account_pk)
    location = JobLocation.objects.get(pk=location_pk)
    job_title = JobTitle.objects.get(pk=job_title_pk)

    job_title_ids = list(
        set(
            [job_title.linkedin_id]
            + list(
                job_title.get_children(recursive=True).values_list(
                    "linkedin_id",
                    flat=True,
                )
            )
        )
    )

    client = account.client

    jobs = []
    limit, chunk, offset, retries = 200, 20, 0, 20

    while True:
        errors = 0

        try:
            new_jobs = client.search_jobs(
                location_geo_id=location.linkedin_geo_id,
                job_title=job_title_ids,
                offset=offset,
                listed_at=24 * 60 * 60,
                limit=chunk,
            )
        except requests.exceptions.JSONDecodeError:
            if errors >= retries:
                raise

            errors += 1
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
    """
    Run search job tasks.
    Break the whole task in smaller parts, to parallel the data loading
    """

    locations = JobLocation.objects.filter(is_active=True).all()
    job_titles = JobTitle.objects.filter(is_active=True, parent__isnull=True).all()

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
    """
    Full process provided jobs

    Args:
        account_pk: LinkedinAccount primary-key
        job_pks: A list of Job primary-keys
    """

    account = LinkedinAccount.objects.get(pk=account_pk)
    jobs = Job.objects.filter(pk__in=job_pks).all()

    client = account.client

    retries = 20
    errors = 0
    resolved_jobs = {}
    while True:
        try:
            resolved_jobs = client.get_jobs_batch(
                jobs.values_list("linkedin_id", flat=True)
            )
            break
        except requests.exceptions.JSONDecodeError:
            if errors >= retries:
                raise
            errors += 1
            default_evade()
            continue

    for job in jobs:
        job_data = resolved_jobs[job.linkedin_id]

        if (not job_data) or (job_data["jobState"] != "LISTED"):
            job.status = JobStatus.EXPIRED
            job.save()
            continue

        try:
            job.company = resolve_company(job_data)
        except NotValidCompanyError:
            job.delete()
            continue

        job.description = job_data["description"]["text"]
        job.attributes = job_data["description"]["attributesV2"]
        job.full_location = job_data["location"]["defaultLocalizedName"]
        job.listed_at = job_data["createdAt"]

        for workplace_type in job_data.get("*jobWorkplaceTypes") or job_data.get(
            "jobWorkplaceTypes", []
        ):
            workplace_type = workplace_type.split(":")[-1]
            if workplace_type == "1":
                job.on_site = True
            if workplace_type == "2":
                job.remote = True
            if workplace_type == "3":
                job.hybrid = True

        # key in description: 1 point
        # key in title: 2 points
        # key+complement in description: 3 points
        # key+title in description: 5 points
        points = 0
        description_contains_keywords, title_contains_keywords = False, False
        _job_title, _job_description = job.title.lower(), job.description.lower()

        for key in settings.LINKEDIN_JOB_DESCRIPTION_KEYWORDS:
            key = key.lower()

            if key in _job_description:
                description_contains_keywords = True
                points += 1

            if key in _job_title:
                title_contains_keywords = True
                points += 2

        for key_complement in settings.LINKEDIN_JOB_DESCRIPTION_KEYWORD_COMPLEMENTS:
            key_complement = key_complement.lower()

            if description_contains_keywords and (key_complement in _job_description):
                points += 3

            if title_contains_keywords and (key_complement in _job_title):
                points += 5

        job.points = points

        if points > 0:
            job.status = JobStatus.WAITING_FOR_REVIEW
        else:
            job.status = JobStatus.REJECTED

        job.save()


@app.task(
    base=Singleton,
    name="job.list_approved_jobs",
    time_limit=10 * 60,
    lock_expiry=10 * 60,
)
def list_approved_jobs():
    account = get_least_used_account()
    client = account.client

    jobs = Job.objects.filter(is_active=True, status=JobStatus.APPROVED)

    for job in jobs:

        errors = 0
        retries = 20
        while True:
            try:
                job_skills = client.get_job_skills(job.linkedin_id)
                break
            except requests.exceptions.JSONDecodeError:
                if errors >= retries:
                    raise

                errors += 1
                default_evade()
                continue

        # noinspection PyUnboundLocalVariable
        for skill_data in job_skills.get("skillMatchStatuses", []):
            skill = skill_data["skill"]
            name = skill["name"]
            linkedin_id = get_id_from_urn(skill["entityUrn"])

            skill_object, skill_created = JobSkill.objects.get_or_create(
                linkedin_id=linkedin_id,
                defaults={"name": name},
            )
            job.job_skills.add(skill_object)

        job.status = JobStatus.LISTED
        job.save()


@app.task(
    base=Singleton,
    name="job.run_process_jobs",
    lock_expiry=60 * 60,
)
def run_process_jobs():
    """
    Run process job tasks.
    Break the whole task in smaller parts, to parallel the data loading
    """

    jobs = (
        Job.objects.filter(is_active=True, status=JobStatus.PARTIALLY_PROCEEDED)
        .order_by("created_at")
        .values_list("pk", flat=True)
        .distinct()
    )

    chunk = 100
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
