"""Unit tests for the operator repository."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.exceptions import OperatorNotFoundError, OperatorRepositoryError
from app.operators.repository import OperatorRepository


def test_repository_loads_default_operators(operators: OperatorRepository) -> None:
    profiles = operators.all()
    ids = {profile.id for profile in profiles}
    assert {"ooredoo_dz", "djezzy_dz", "mobilis_dz"} <= ids


def test_repository_match_by_imsi(operators: OperatorRepository) -> None:
    profile = operators.match(imsi="603021234567890")
    assert profile is not None
    assert profile.id == "ooredoo_dz"


def test_repository_match_by_iccid(operators: OperatorRepository) -> None:
    profile = operators.match(imsi=None, iccid="8921301234567890123")
    assert profile is not None
    assert profile.id == "djezzy_dz"


def test_repository_require_raises_on_missing(operators: OperatorRepository) -> None:
    with pytest.raises(OperatorNotFoundError):
        operators.require("does_not_exist")


def test_repository_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(OperatorRepositoryError):
        OperatorRepository.from_file(tmp_path / "missing.json")


def test_repository_rejects_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(OperatorRepositoryError):
        OperatorRepository.from_file(bad)


def test_repository_filters_by_country(operators: OperatorRepository) -> None:
    dz = operators.by_country("DZ")
    assert len(dz) == 3
    assert {p.country_code for p in dz} == {"DZ"}
