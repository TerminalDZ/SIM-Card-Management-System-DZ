"""Read-only repository for :class:`OperatorProfile` objects.

Profiles are loaded from a JSON file at startup. Validation runs through
Pydantic so a malformed file fails the process at boot, not on the first
request.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from app.core.exceptions import OperatorNotFoundError, OperatorRepositoryError
from app.core.logger import get_logger
from app.schemas.operator import OperatorProfile


class OperatorRepository:
    """In-memory operator profiles with index-based lookup helpers."""

    def __init__(self, profiles: Iterable[OperatorProfile]) -> None:
        self._logger = get_logger("operators")
        self._profiles: dict[str, OperatorProfile] = {p.id: p for p in profiles}
        self._logger.info("Loaded %d operator profile(s)", len(self._profiles))

    # ── Construction ────────────────────────────────────────────────────────
    @classmethod
    def from_file(cls, path: Path) -> OperatorRepository:
        if not path.exists():
            raise OperatorRepositoryError(
                f"Operator registry not found at {path}",
                details={"path": str(path)},
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OperatorRepositoryError(
                f"Invalid operator registry at {path}: {exc}",
                details={"path": str(path)},
            ) from exc
        items = data.get("operators") if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise OperatorRepositoryError(
                "Operator registry must be a list (or {operators: [...]})",
                details={"path": str(path)},
            )
        try:
            profiles = [OperatorProfile.model_validate(item) for item in items]
        except ValidationError as exc:
            raise OperatorRepositoryError(
                f"Operator registry has invalid entries: {exc.errors()}",
                details={"path": str(path)},
            ) from exc
        return cls(profiles)

    # ── Lookups ─────────────────────────────────────────────────────────────
    def __len__(self) -> int:
        return len(self._profiles)

    def __iter__(self) -> Iterable[OperatorProfile]:
        return iter(self._profiles.values())

    def all(self) -> list[OperatorProfile]:
        return list(self._profiles.values())

    def get(self, operator_id: str) -> OperatorProfile | None:
        return self._profiles.get(operator_id)

    def require(self, operator_id: str) -> OperatorProfile:
        profile = self.get(operator_id)
        if profile is None:
            raise OperatorNotFoundError(
                f"Operator {operator_id!r} is not in the registry",
                details={"operator_id": operator_id},
            )
        return profile

    def match(self, *, imsi: str | None = None, iccid: str | None = None) -> OperatorProfile | None:
        """Return the first profile matching IMSI then ICCID prefixes."""
        if imsi:
            for profile in self._profiles.values():
                if profile.matches_imsi(imsi):
                    return profile
        if iccid:
            for profile in self._profiles.values():
                if profile.matches_iccid(iccid):
                    return profile
        return None

    def by_country(self, country_code: str) -> list[OperatorProfile]:
        target = country_code.upper()
        return [
            profile for profile in self._profiles.values() if profile.country_code.upper() == target
        ]
