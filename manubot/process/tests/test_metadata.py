import copy

import pytest


from ..metadata import get_header_includes, get_thumbnail_url, get_manuscript_urls
from ..ci import get_continuous_integration_parameters


def test_get_header_includes_description_abstract():
    # test that abstract and description set different fields if both supplied
    variables = {
        "pandoc": {"abstract": "value for abstract"},
        "manubot": {"description": "value for description"},
    }
    header_includes = get_header_includes(copy.deepcopy(variables))
    assert (
        '<meta name="citation_abstract" content="value for abstract" />'
        in header_includes
    )
    assert (
        '<meta name="description" content="value for description" />' in header_includes
    )
    # test that abstract is used for description if description is not defined
    del variables["manubot"]["description"]
    header_includes = get_header_includes(copy.deepcopy(variables))
    assert (
        '<meta name="citation_abstract" content="value for abstract" />'
        in header_includes
    )
    assert '<meta name="description" content="value for abstract" />' in header_includes
    # test that if neither abstract nor description is defined, neither are inserted
    del variables["pandoc"]["abstract"]
    header_includes = get_header_includes(copy.deepcopy(variables))
    assert 'meta name="citation_abstract"' not in header_includes
    assert 'meta name="description"' not in header_includes


ci_params = get_continuous_integration_parameters() or {}
local_only = pytest.mark.skipif(
    ci_params, reason="skipping on local build since test assumes supported CI behavior"
)
ci_only = pytest.mark.skipif(
    not ci_params, reason="skipping on CI build since test assumes local behavior"
)

repo_raw_url_template = (
    f"https://github.com/{ci_params.get('repo_slug', '')}"
    f"/raw/{ci_params.get('triggering_commit', '')}/"
)
example_thumbnail_url = (
    repo_raw_url_template + "manubot/process/tests/manuscripts/example/thumbnail.png"
)


@pytest.mark.parametrize(
    ("thumbnail", "expected"),
    [
        pytest.param(None, None, id="None-on-local", marks=local_only),
        pytest.param("", None, id="empty-on-local", marks=local_only),
        pytest.param(None, example_thumbnail_url, id="None-on-ci", marks=ci_only),
        pytest.param("", example_thumbnail_url, id="empty-on-ci", marks=ci_only),
        pytest.param(
            "path/to/thumbnail.png", None, id="local-path-on-local", marks=local_only
        ),
        pytest.param(
            "path/to/thumbnail.png",
            repo_raw_url_template + "path/to/thumbnail.png",
            id="local-path-on-ci",
            marks=ci_only,
        ),
        pytest.param(
            "http://example.com/thumbnail.png",
            "http://example.com/thumbnail.png",
            id="url-http",
        ),
        pytest.param(
            "https://example.com/thumbnail.png",
            "https://example.com/thumbnail.png",
            id="url-https",
        ),
    ],
)
def test_get_thumbnail_url(thumbnail, expected):
    thumbnail_url = get_thumbnail_url(thumbnail)
    assert expected == thumbnail_url


@pytest.mark.parametrize(
    ("html_url", "expected"),
    [
        pytest.param(None, {}, id="html_url-none-local", marks=local_only),
        pytest.param(
            "https://example.com/manuscript/",
            {
                "html_url": "https://example.com/manuscript/",
                "pdf_url": "https://example.com/manuscript/manuscript.pdf",
            },
            id="html_url-set-local",
            marks=local_only,
        ),
        pytest.param(
            None,
            {
                "html_url": "https://manubot.github.io/manubot/",
                "pdf_url": "https://manubot.github.io/manubot/manuscript.pdf",
                "html_url_versioned": f"https://manubot.github.io/manubot/v/{ci_params.get('commit')}/",
                "pdf_url_versioned": f"https://manubot.github.io/manubot/v/{ci_params.get('commit')}/manuscript.pdf",
            },
            id="html_url-none-ci",
            marks=ci_only,
        ),
        pytest.param(
            "https://example.com/manuscript/",
            {
                "html_url": "https://example.com/manuscript/",
                "pdf_url": "https://example.com/manuscript/manuscript.pdf",
                "html_url_versioned": f"https://example.com/manuscript/v/{ci_params.get('commit')}/",
                "pdf_url_versioned": f"https://example.com/manuscript/v/{ci_params.get('commit')}/manuscript.pdf",
            },
            id="html_url-set-ci",
            marks=ci_only,
        ),
    ],
)
def test_get_manuscript_urls(html_url, expected):
    urls = get_manuscript_urls(html_url)
    assert urls == expected
