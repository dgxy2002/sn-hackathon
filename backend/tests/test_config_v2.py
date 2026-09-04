import pytest

from app.config import ConfigurationError, Settings


def test_v2_document_settings_have_privacy_safe_defaults_and_overrides() -> None:
    defaults = Settings.from_env({"APP_ENV": "test"})

    assert defaults.analysis_ttl_hours == 24
    assert defaults.document_max_size_bytes == 20 * 1024 * 1024
    assert defaults.document_max_page_count == 100
    assert defaults.document_orphan_ttl_minutes == 30
    assert defaults.document_workspace_root is None

    configured = Settings.from_env(
        {
            "APP_ENV": "test",
            "ANALYSIS_TTL_HOURS": "12",
            "DOCUMENT_MAX_SIZE_BYTES": "1048576",
            "DOCUMENT_MAX_PAGE_COUNT": "25",
            "DOCUMENT_ORPHAN_TTL_MINUTES": "15",
            "DOCUMENT_WORKSPACE_ROOT": "/tmp/private-documents",
        }
    )

    assert configured.analysis_ttl_hours == 12
    assert configured.document_max_size_bytes == 1048576
    assert configured.document_max_page_count == 25
    assert configured.document_orphan_ttl_minutes == 15
    assert configured.document_workspace_root == "/tmp/private-documents"


@pytest.mark.parametrize(
    "name",
    [
        "ANALYSIS_TTL_HOURS",
        "DOCUMENT_MAX_SIZE_BYTES",
        "DOCUMENT_MAX_PAGE_COUNT",
        "DOCUMENT_ORPHAN_TTL_MINUTES",
    ],
)
def test_v2_document_settings_reject_non_positive_values(name: str) -> None:
    with pytest.raises(ConfigurationError, match=name):
        Settings.from_env({"APP_ENV": "test", name: "0"})