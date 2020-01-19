"""
Utilities for accessing <https://unpaywall.org/> data to provide access
information for DOIs.
"""
import requests
from manubot.util import contact_email


class Unpaywall_DOI:
    """
    From https://unpaywall.org/data-format:

    > The DOI object is more or less a row in our main database...
    it's everything we know about a given DOI-assigned resource,
    including metadata about the resource itself,
    and information about its OA status.
    It includes a list of zero or more OA Location Objects,
    as well as a `best_oa_location` property that's probably the OA Location you'll want to use.
    """

    def __init__(self, doi):
        self.doi = doi.lower()
        self.query_unpaywall_api()

    def query_unpaywall_api(self):
        url = f"https://api.unpaywall.org/v2/{self.doi}"
        params = {"email": contact_email}
        response = requests.get(url, params=params)
        self.results = response.json()
        self.locations = [
            Unpaywall_Location(location)
            for location in self.results.get("oa_locations", [])
        ]

    @property
    def best_openly_licensed_pdf(self) -> "Unpaywall_Location":
        for location in self.locations:
            if location.has_openly_licensed_pdf:
                return location

    @property
    def best_pdf(self) -> "Unpaywall_Location":
        for location in self.locations:
            if location.has_pdf:
                return location


class Unpaywall_Location(dict):
    """
    From https://unpaywall.org/data-format

    > The OA Location object describes particular place where we found a given OA article.
    The same article is often available from multiple locations,
    and there may be differences in format, version, and license depending on the location;
    the OA Location object describes these key attributes.
    An OA Location Object is always a Child of a DOI Object.
    """

    open_licenses = {"cc-by", "cc0"}

    @property
    def has_pdf(self):
        return bool(self.get("url_for_pdf"))

    @property
    def has_open_license(self):
        license = self.get("license")
        return license in self.open_licenses

    @property
    def has_creative_commons_license(self):
        license = self.get("license")
        if not license:
            return False
        return license == "cc0" or license.startswith("cc-")

    @property
    def has_openly_licensed_pdf(self):
        return self.has_pdf and self.has_open_license
