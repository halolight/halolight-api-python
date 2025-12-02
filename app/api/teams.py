"""Team management routes matching API spec."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import User
from app.schemas.team import (
    AddMemberRequest,
    MemberBasic,
    OwnerBasic,
    RemoveMemberResponse,
    TeamCreate,
    TeamDetailResponse,
    TeamListResponse,
    TeamResponse,
    TeamUpdate,
)
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=TeamListResponse)
async def list_teams(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TeamListResponse:
    """Get all teams for current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of teams
    """
    team_service = TeamService(db)
    teams = team_service.get_user_teams(current_user.id)

    team_responses = []
    for team in teams:
        member_count = team_service.get_member_count(team.id)
        team_responses.append(
            TeamResponse(
                id=team.id,
                name=team.name,
                description=team.description,
                avatar=team.avatar,
                owner=OwnerBasic(id=team.owner.id, name=team.owner.name),
                memberCount=member_count,
                created_at=team.created_at,
            )
        )

    return TeamListResponse(data=team_responses)


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TeamDetailResponse:
    """Get team by ID with members.

    Args:
        team_id: Team ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Team data with members

    Raises:
        HTTPException: If team not found
    """
    team_service = TeamService(db)
    team = team_service.get_by_id(team_id, with_members=True)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    member_count = team_service.get_member_count(team.id)
    members = [
        MemberBasic(
            id=tm.user.id,
            name=tm.user.name,
            email=tm.user.email,
            avatar=tm.user.avatar,
            role=tm.role.name if tm.role else None,
        )
        for tm in team.members
    ]

    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        avatar=team.avatar,
        owner=OwnerBasic(id=team.owner.id, name=team.owner.name),
        memberCount=member_count,
        created_at=team.created_at,
        members=members,
    )


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TeamResponse:
    """Create a new team.

    Args:
        team_data: Team creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created team
    """
    team_service = TeamService(db)
    team = team_service.create(team_data, current_user.id)

    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        avatar=team.avatar,
        owner=OwnerBasic(id=team.owner.id, name=team.owner.name),
        memberCount=0,
        created_at=team.created_at,
    )


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TeamResponse:
    """Update team information.

    Args:
        team_id: Team ID
        team_data: Team update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated team

    Raises:
        HTTPException: If team not found or user is not owner
    """
    team_service = TeamService(db)

    # Check ownership
    if not team_service.is_owner(team_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can update team",
        )

    team = team_service.update(team_id, team_data)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    member_count = team_service.get_member_count(team.id)

    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        avatar=team.avatar,
        owner=OwnerBasic(id=team.owner.id, name=team.owner.name),
        memberCount=member_count,
        created_at=team.created_at,
    )


@router.post("/{team_id}/members", response_model=TeamDetailResponse)
async def add_member(
    team_id: str,
    member_data: AddMemberRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> TeamDetailResponse:
    """Add a member to a team.

    Args:
        team_id: Team ID
        member_data: Member data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated team with members

    Raises:
        HTTPException: If team not found or user is not owner
    """
    team_service = TeamService(db)

    # Check ownership
    if not team_service.is_owner(team_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can add members",
        )

    member = team_service.add_member(team_id, member_data.userId, member_data.roleId)

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team or user not found",
        )

    # Return updated team
    team = team_service.get_by_id(team_id, with_members=True)
    member_count = team_service.get_member_count(team.id)
    members = [
        MemberBasic(
            id=tm.user.id,
            name=tm.user.name,
            email=tm.user.email,
            avatar=tm.user.avatar,
            role=tm.role.name if tm.role else None,
        )
        for tm in team.members
    ]

    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        avatar=team.avatar,
        owner=OwnerBasic(id=team.owner.id, name=team.owner.name),
        memberCount=member_count,
        created_at=team.created_at,
        members=members,
    )


@router.delete("/{team_id}/members/{user_id}", response_model=RemoveMemberResponse)
async def remove_member(
    team_id: str,
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RemoveMemberResponse:
    """Remove a member from a team.

    Args:
        team_id: Team ID
        user_id: User ID to remove
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If team not found, user is not owner, or member not found
    """
    team_service = TeamService(db)

    # Check ownership
    if not team_service.is_owner(team_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can remove members",
        )

    removed = team_service.remove_member(team_id, user_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in team",
        )

    return RemoveMemberResponse(
        message="Member successfully removed",
        teamId=team_id,
        userId=user_id,
    )


@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete team.

    Args:
        team_id: Team ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If team not found or user is not owner
    """
    team_service = TeamService(db)

    # Check ownership
    if not team_service.is_owner(team_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can delete team",
        )

    deleted = team_service.delete(team_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    return {"message": "Team successfully deleted", "id": team_id}
