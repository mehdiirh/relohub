import json

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect

from job.models import JobTitle


@login_required
@permission_required(["job.add_job_title"])
def add_job_titles(request):

    if request.method == "GET":
        with open(settings.BASE_DIR / "keys.json") as f:
            data = json.load(f)

        job_titles = JobTitle.objects.filter(parent__isnull=True).all()

        all_titles = JobTitle.objects.none()
        for child in job_titles:
            all_titles |= child.get_children(recursive=True)

        all_titles |= job_titles

        data = dict(
            filter(
                lambda x: x[0]
                not in all_titles.values_list("linkedin_id", flat=True).distinct(),
                data.items(),
            )
        )

        context = {"data": data, "titles": job_titles}

        return render(
            request, "linkedin/admin_pages/add_job_title.html", context=context
        )

    if request.method == "POST":
        name: str = request.POST.get("name")
        parent = request.POST.get("parent")
        linkedin_id = request.POST.get("linkedin-id")
        action = request.POST.get("action")

        data = json.load(open(settings.BASE_DIR / "keys.json"))

        if action == "DELETE":
            del data[linkedin_id]
            json.dump(data, open(settings.BASE_DIR / "keys.json", "w"), indent=4)
            return redirect("add-job-title")

        entity = data[linkedin_id]

        if not name and parent:
            title = JobTitle.objects.get(pk=parent)

        else:
            title, created = JobTitle.objects.get_or_create(
                linkedin_id=linkedin_id,
                defaults={
                    "parent_id": parent,
                    "title": name.title(),
                },
            )

        for val in entity:
            if val.lower() != name.lower():
                title.add_other_name(val)
                title.add_other_name(val.title().replace(" ", ""))
                title.add_other_name(val.title().replace(" ", "-"))
                title.add_other_name(val.title().replace(" ", "_"))

        title.add_other_name(name.title().replace(" ", ""))
        title.add_other_name(name.title().replace(" ", "-"))
        title.add_other_name(name.title().replace(" ", "_"))

        return redirect("add-job-title")
