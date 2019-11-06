import pytest


from ..thumbnail import get_thumbnail_url
from ..ci import get_continuous_integration_parameters

ci_params = get_continuous_integration_parameters() or {}
local_only = pytest.mark.skipif(
    ci_params, reason="skipping on local build since test assumes supported CI behavior"
)
ci_only = pytest.mark.skipif(
    not ci_params, reason="skipping on CI build since test assumes local behavior"
)

repo_raw_url_template = (
    f"https://github.com/manubot/manubot/raw/{ci_params.get('triggering_commit', '')}/"
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
    print(ci_params)
    thumbnail_url = get_thumbnail_url(thumbnail)
    assert expected == thumbnail_url
