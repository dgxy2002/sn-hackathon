from datetime import date

import pytest
from pydantic import ValidationError

from app.contracts import ProfileData, VersionedProfile
from tests.factories import field, make_profile


def test_profile_contract_distinguishes_zero_unknown_and_no_policy() -> None:
    profile = make_profile()

    assert profile.data.dependant_count.state == "present"
    assert profile.data.dependant_count.value == 0
    assert profile.data.existing_death_cover.state == "unknown"
    assert profile.data.existing_death_cover.value is None
    assert profile.data.has_current_policy.value is False


def test_profile_contract_rejects_state_value_conflicts() -> None:
    with pytest.raises(ValidationError, match="cannot have a value"):
        field(0, state="unknown")

    with pytest.raises(ValidationError, match="require a value"):
        field(None, state="present")


def test_profile_contract_rejects_wrong_types_and_versions() -> None:
    values = make_profile().data.model_dump()
    values["monthly_budget"]["value"] = "180"
    with pytest.raises(ValidationError):
        ProfileData.model_validate(values)

    with pytest.raises(ValidationError):
        VersionedProfile(
            schema_id="covercheck.profile",
            contract_version="2.0.0",
            profile_id="profile-fixture-001",
            version=1,
            as_of_date=date(2026, 8, 28),
            consent=True,
            data=make_profile().data,
        )