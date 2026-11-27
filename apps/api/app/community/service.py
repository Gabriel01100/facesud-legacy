import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.community import MembershipStatus, OrganizationUnit, UnitMembership, UnitStatus
from app.models.identity import Account, AccountStatus


class CommunityRuleError(Exception):
    pass


def list_active_units(db: Session) -> list[OrganizationUnit]:
    return list(db.scalars(
        select(OrganizationUnit).where(OrganizationUnit.status == UnitStatus.ACTIVE)
        .order_by(OrganizationUnit.country_code, OrganizationUnit.name)
    ))


def create_unit(db: Session, *, name: str, unit_type, country_code: str, parent_id, administrative_area, locality):
    if parent_id is not None:
        parent = db.scalar(select(OrganizationUnit).where(OrganizationUnit.id == parent_id).with_for_update())
        if parent is None or parent.status != UnitStatus.ACTIVE:
            raise CommunityRuleError("Parent unit does not exist or is inactive.")
        allowed_parent = {"branch": {"stake", "ward"}, "ward": {"stake"}, "stake": set()}
        if parent.unit_type.value not in allowed_parent[unit_type.value]:
            raise CommunityRuleError("Invalid parent unit type.")
        if parent.country_code != country_code:
            raise CommunityRuleError("Parent and child units must belong to the same country.")
    unit = OrganizationUnit(
        name=name, unit_type=unit_type, country_code=country_code, parent_id=parent_id,
        administrative_area=administrative_area, locality=locality, status=UnitStatus.ACTIVE,
    )
    db.add(unit)
    db.flush()
    return unit


def request_membership(db: Session, account_id: uuid.UUID, unit_id: uuid.UUID) -> UnitMembership:
    account = db.scalar(select(Account).where(Account.id == account_id).with_for_update())
    if account is None or account.status != AccountStatus.ACTIVE:
        raise CommunityRuleError("An active account is required.")
    unit = db.scalar(select(OrganizationUnit).where(
        OrganizationUnit.id == unit_id, OrganizationUnit.status == UnitStatus.ACTIVE
    ))
    if unit is None:
        raise CommunityRuleError("Unit not found or inactive.")
    existing_pending = db.scalar(select(UnitMembership).where(
        UnitMembership.account_id == account_id, UnitMembership.status == MembershipStatus.PENDING,
    ))
    if existing_pending:
        raise CommunityRuleError("A pending community request already exists.")
    approved = db.scalar(select(UnitMembership).where(
        UnitMembership.account_id == account_id, UnitMembership.status == MembershipStatus.APPROVED,
    ))
    if approved:
        raise CommunityRuleError("An approved community link already exists.")
    request = UnitMembership(account_id=account_id, unit_id=unit_id, status=MembershipStatus.PENDING)
    db.add(request)
    db.flush()
    return request


def get_own_memberships(db: Session, account_id: uuid.UUID) -> list[tuple[UnitMembership, OrganizationUnit]]:
    rows = db.execute(
        select(UnitMembership, OrganizationUnit)
        .join(OrganizationUnit, OrganizationUnit.id == UnitMembership.unit_id)
        .where(UnitMembership.account_id == account_id)
        .order_by(UnitMembership.requested_at.desc())
    )
    return list(rows)


def list_review_requests(db: Session) -> list[tuple[UnitMembership, OrganizationUnit, Account]]:
    rows = db.execute(
        select(UnitMembership, OrganizationUnit, Account)
        .join(OrganizationUnit, OrganizationUnit.id == UnitMembership.unit_id)
        .join(Account, Account.id == UnitMembership.account_id)
        .where(UnitMembership.status == MembershipStatus.PENDING)
        .order_by(UnitMembership.requested_at.asc())
        .limit(100)
    )
    return list(rows)


def review_membership(
    db: Session, *, request_id: uuid.UUID, reviewer_id: uuid.UUID, decision: MembershipStatus, note: str | None
) -> UnitMembership:
    request = db.scalar(select(UnitMembership).where(UnitMembership.id == request_id).with_for_update())
    if request is None or request.status != MembershipStatus.PENDING:
        raise CommunityRuleError("Pending request not found.")
    if decision == MembershipStatus.APPROVED:
        approved = db.scalar(select(UnitMembership).where(
            UnitMembership.account_id == request.account_id, UnitMembership.status == MembershipStatus.APPROVED,
        ))
        if approved:
            raise CommunityRuleError("This account already has an approved community link.")
    request.status = decision
    request.reviewed_at = datetime.now(timezone.utc)
    request.reviewer_account_id = reviewer_id
    request.review_note = note.strip() if note and note.strip() else None
    db.flush()
    return request
