"""
Utilities for accessing <https://unpaywall.org/> data to provide access
information for DOIs. Also supports identifier sources not directly
supported by Unpaywall, such as arXiv IDs.
"""
import abc

import requests

"""
Unpaywall license choices used by Location.has_open_license.
Defaults to licenses that conform to <https://opendefinition.org/>.
"""
open_licenses = {"cc0", "cc-by", "cc-by-sa", "pd"}


class Unpaywall:
    """
    A class to handle open access locations in the Unpaywall data format.
    Create new Unpaywall objects using the `from_csl_item` and `from_citekey` methods,
    or by using __init__ of a subclass like `Unpaywall_DOI`.
    """

    csl_item = None

    @abc.abstractmethod
    def set_oa_locations(self):
        """
        Set `self.oa_locations`, which is a list of `Unpaywall_Location` objects.
        """
        self.oa_locations = []

    @property
    def best_openly_licensed_pdf(self) -> "Unpaywall_Location":
        for location in self.oa_locations:
            if location.has_openly_licensed_pdf:
                return location

    @property
    def best_pdf(self) -> "Unpaywall_Location":
        for location in self.oa_locations:
            if location.has_pdf:
                return location

    @staticmethod
    def from_citekey(citekey, csl_item=None):
        """
        Create an Unpaywall object for `citekey`.
        `csl_item` is an optional field that can avoid an
        external web request to generate to a new CSL Item.
        """
        from .citekey import CiteKey

        if isinstance(citekey, str):
            citekey = CiteKey(citekey)
        if not isinstance(citekey, CiteKey):
            raise ValueError("citekey must be a str or CiteKey")
        if citekey.standard_prefix in source_to_unpaywaller:
            unpaywaller = source_to_unpaywaller[citekey.standard_prefix]
            unpaywall = unpaywaller(citekey.standard_accession, set_oa_locations=False)
        else:
            raise ValueError(
                f"Cannot Unpaywall {citekey.input_id}. "
                f"Supported citations sources are {', '.join(source_to_unpaywaller)}. "
                "Received {citekey.standard_prefix!r}."
            )
        unpaywall.csl_item = csl_item
        unpaywall.set_oa_locations()
        return unpaywall

    @classmethod
    def from_csl_item(cls, csl_item):
        """
        Create an Unpaywall object for `csl_item`.
        """
        from .csl_item import CSL_Item

        csl_item = CSL_Item(csl_item)
        doi = csl_item.get("DOI")
        if doi:
            return cls.from_citekey(f"doi:{doi}", csl_item=csl_item)
        csl_item.infer_id()
        return cls.from_citekey(csl_item["id"], csl_item=csl_item)


class Unpaywall_DOI(Unpaywall):
    """
    From https://unpaywall.org/data-format:

    > The DOI object is more or less a row in our main database...
    it's everything we know about a given DOI-assigned resource,
    including metadata about the resource itself,
    and information about its OA status.
    It includes a list of zero or more OA Location Objects,
    as well as a `best_oa_location` property that's probably the OA Location you'll want to use.
    """

    def __init__(self, doi, set_oa_locations=True):
        self.doi = doi.lower()
        if set_oa_locations:
            self.set_oa_locations()

    def set_oa_locations(self):
        from manubot.util import contact_email

        url = f"https://api.unpaywall.org/v2/{self.doi}"
        params = {"email": contact_email}
        response = requests.get(url, params=params)
        response.raise_for_status()
        self.results = response.json()
        self.oa_locations = [
            Unpaywall_Location(location)
            for location in self.results.get("oa_locations", [])
        ]


class Unpaywall_arXiv(Unpaywall):
    def __init__(self, arxiv_id, set_oa_locations=True, use_doi=True):
        from .arxiv import split_arxiv_id_version

        self.arxiv_id = arxiv_id
        self.arxiv_id_latest, self.arxiv_id_version = split_arxiv_id_version(arxiv_id)
        self.use_doi = use_doi
        if set_oa_locations:
            self.set_oa_locations()

    def set_oa_locations(self):
        from .arxiv import get_arxiv_csl_item

        if not self.csl_item:
            self.csl_item = get_arxiv_csl_item(self.arxiv_id)
        doi = self.csl_item.get("DOI")
        if self.use_doi and doi:
            unpaywall_doi = Unpaywall_DOI(doi)
            self.doi = unpaywall_doi.doi
            self.oa_locations = unpaywall_doi.oa_locations
            return
        location = self.location_from_arvix_id()
        self.oa_locations = [location]

    def location_from_arvix_id(self):
        import datetime

        url_for_pdf = f"https://arxiv.org/pdf/{self.arxiv_id}.pdf"
        location = Unpaywall_Location(
            {
                "endpoint_id": None,
                "evidence": "oa repository",
                "host_type": "repository",
                "is_best": True,
                "license": self.get_license(),
                "pmh_id": f"oai:arXiv.org:{self.arxiv_id_latest}",
                "repository_institution": "Cornell University - arXiv",
                "updated": datetime.datetime.now().isoformat(),
                "url": url_for_pdf,
                "url_for_landing_page": f"https://arxiv.org/abs/{self.arxiv_id}",
                "url_for_pdf": url_for_pdf,
                "version": "submittedVersion",
            }
        )
        return location

    def get_license(self):
        """
        Return license using choices from the Unpaywall data format.
        Looks for license metadata in the CSL Item.
        """
        license = self.csl_item.note_dict.get("license")
        if not license:
            return
        # Example licenses from https://arxiv.org/help/license
        # http://creativecommons.org/publicdomain/zero/1.0/
        # http://creativecommons.org/licenses/by/4.0/
        # http://creativecommons.org/licenses/by-sa/4.0/
        # http://creativecommons.org/licenses/by-nc-sa/4.0/
        # http://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html
        from urllib.parse import urlparse

        parsed_url = urlparse(license)
        if not parsed_url.scheme.startswith("http"):
            return
        if parsed_url.hostname.endswith("creativecommons.org"):
            try:
                abbrev = parsed_url.path.split("/")[2]
            except IndexError:
                return
            if abbrev == "zero":
                return "cc0"
            return f"cc-{abbrev}"


source_to_unpaywaller = {
    "doi": Unpaywall_DOI,
    "arxiv": Unpaywall_arXiv,
}


class Unpaywall_Location(dict):
    """
    From https://unpaywall.org/data-format

    > The OA Location object describes particular place where we found a given OA article.
    The same article is often available from multiple locations,
    and there may be differences in format, version, and license depending on the location;
    the OA Location object describes these key attributes.
    An OA Location Object is always a Child of a DOI Object.

    Example oa_locations from the Unpaywall API are:

    ```json
    {
        "endpoint_id": null,
        "evidence": "open (via page says license)",
        "host_type": "publisher",
        "is_best": true,
        "license": "cc-by",
        "pmh_id": null,
        "repository_institution": null,
        "updated": "2020-01-19T08:55:45.548214",
        "url": "https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1007250&type=printable",
        "url_for_landing_page": "https://doi.org/10.1371/journal.pcbi.1007250",
        "url_for_pdf": "https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1007250&type=printable",
        "version": "publishedVersion"
    },
    {
        "endpoint_id": "ca8f8d56758a80a4f86",
        "evidence": "oa repository (via OAI-PMH doi match)",
        "host_type": "repository",
        "is_best": true,
        "license": null,
        "pmh_id": "oai:arXiv.org:1806.05726",
        "repository_institution": "Cornell University - arXiv",
        "updated": "2019-11-01T00:28:16.784912",
        "url": "http://arxiv.org/pdf/1806.05726",
        "url_for_landing_page": "http://arxiv.org/abs/1806.05726",
        "url_for_pdf": "http://arxiv.org/pdf/1806.05726",
        "version": "submittedVersion"
    }
    ```
    """

    @property
    def has_pdf(self):
        return bool(self.get("url_for_pdf"))

    @property
    def has_open_license(self):
        license = self.get("license")
        return license in open_licenses

    @property
    def has_creative_commons_license(self):
        license = self.get("license")
        if not license:
            return False
        return license == "cc0" or license.startswith("cc-")

    @property
    def has_openly_licensed_pdf(self):
        return self.has_pdf and self.has_open_license
