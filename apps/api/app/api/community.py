from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.identity import get_current_session, require_csrf
from app.api.schemas.community import (
    MembershipRequestCreate, MembershipResponse, MembershipReviewRequest,
    ReviewQueueItem, UnitCreateRequest, UnitResponse,
)
from app.community.service import (
    CommunityRuleError, create_unit, get_own_memberships, list_active_units,
    list_review_requests, request_membership, review_membership,
)
from app.core.config import settings
from app.core.database import get_db
from app.models.community import OrganizationUnit, UnitMembership
from app.models.identity import Account, UserSession

router = APIRouter(prefix="/api/v1/community", tags=["community"])


def _unit(unit: OrganizationUnit) -> UnitResponse:
    return UnitResponse(
        id=unit.id, parent_id=unit.parent_id, unit_type=unit.unit_type, name=unit.name,
        country_code=unit.country_code, administrative_area=unit.administrative_area, locality=unit.locality,
    )


def _membership(request: UnitMembership, unit: OrganizationUnit) -> MembershipResponse:
    return MembershipResponse(
        id=request.id, unit=_unit(unit), status=request.status, requested_at=request.requested_at,
        reviewed_at=request.reviewed_at, provisional=True,
    )


def _require_reviewer(session: UserSession, db: Session) -> None:
    account = db.get(Account, session.account_id)
    allowed = {email.strip().lower() for email in settings.community_reviewer_emails.split(",") if email.strip()}
    if account is None or account.email_normalized not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Community reviewer permission required.")


@router.get("/units", response_model=list[UnitResponse])
def get_units(db: Session = Depends(get_db)):
    return [_unit(unit) for unit in list_active_units(db)]


@router.post("/units", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def add_unit(
    data: UnitCreateRequest,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    _require_reviewer(session, db)
    try:
        unit = create_unit(
            db, name=data.name, unit_type=data.unit_type, country_code=data.country_code,
            parent_id=data.parent_id, administrative_area=data.administrative_area, locality=data.locality,
        )
        return _unit(unit)
    except CommunityRuleError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.post("/membership-requests", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
def create_membership_request(
    data: MembershipRequestCreate,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    try:
        request = request_membership(db, session.account_id, data.unit_id)
        unit = db.get(OrganizationUnit, request.unit_id)
        return _membership(request, unit)
    except CommunityRuleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/membership/me", response_model=list[MembershipResponse])
def my_memberships(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    return [_membership(request, unit) for request, unit in get_own_memberships(db, session.account_id)]


@router.get("/review/requests", response_model=list[ReviewQueueItem])
def review_queue(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    _require_reviewer(session, db)
    return [
        ReviewQueueItem(
            id=request.id, unit=_unit(unit), status=request.status,
            requested_at=request.requested_at, account_reference=account.email_normalized,
        )
        for request, unit, account in list_review_requests(db)
    ]


@router.post("/review/requests/{request_id}", response_model=MembershipResponse)
def decide_request(
    request_id: str,
    data: MembershipReviewRequest,
    session: UserSession = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    _require_reviewer(session, db)
    import uuid
    try:
        parsed_id = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Request not found.") from None
    try:
        request = review_membership(
            db, request_id=parsed_id, reviewer_id=session.account_id, decision=data.decision, note=data.note,
        )
        unit = db.get(OrganizationUnit, request.unit_id)
        return _membership(request, unit)
    except CommunityRuleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
