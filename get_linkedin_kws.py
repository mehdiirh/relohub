import json
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "relohub.settings")
django.setup()

#####

from linkedin.models import LinkedinAccount
from linkedin_api.utils.helpers import get_id_from_urn


def get_linkedin_keywords(keyword: str):
    client = LinkedinAccount.objects.get(pk=1).client

    query = f"(keywords:{keyword},query:(showFullLastNameForConnections:true,typeaheadFilterQuery:()),type:TITLE)"

    res = client._fetch(
        f"/graphql?variables={query}&queryId=voyagerSearchDashReusableTypeahead.9b1a5196b62c860b36dea4440f6d630f",
        headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
    )
    data = res.json()
    elements = data["data"]["data"]["searchDashReusableTypeaheadByType"]["elements"]

    titles = {}

    for element in elements:
        title_id = get_id_from_urn(element["trackingUrn"])
        text = element["title"]["text"]

        _title = titles.get(title_id, [])
        _title.append(text)

        titles[title_id] = _title

    return titles


all_titles = {}
while True:

    keyword = input("Enter keyword: ")

    try:
        titles = get_linkedin_keywords(keyword)
        print(len(titles), "titles found")
        all_titles.update(titles)
    except KeyboardInterrupt:
        raise
    finally:
        data = json.load(open("keys.json", "r"))
        data.update(all_titles)
        json.dump(data, open("keys.json", "w"), indent=4)
