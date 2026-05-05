"""Read-only endpoints for the operator registry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path

from app.api.deps import OperatorsDep
from app.schemas.operator import OperatorProfile

router = APIRouter(prefix="/api/operators", tags=["Operators"])


@router.get("", response_model=list[OperatorProfile])
async def list_operators(operators: OperatorsDep) -> list[OperatorProfile]:
    return operators.all()


@router.get("/{operator_id}", response_model=OperatorProfile)
async def get_operator(
    operators: OperatorsDep,
    operator_id: str = Path(..., min_length=1),
) -> OperatorProfile:
    profile = operators.get(operator_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Operator {operator_id!r} not found")
    return profile
