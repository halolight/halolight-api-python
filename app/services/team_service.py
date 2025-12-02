"""Team service for business logic."""

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import Team, TeamMember, User
from app.models.base import generate_cuid
from app.schemas.team import TeamCreate, TeamUpdate


class TeamService:
    """Team service for managing team operations."""

    def __init__(self, db: Session) -> None:
        """Initialize team service.

        Args:
            db: Database session
        """
        self.db = db

    def get_by_id(self, team_id: str, with_members: bool = False) -> Team | None:
        """Get team by ID.

        Args:
            team_id: Team ID
            with_members: Whether to eager load members

        Returns:
            Team or None if not found
        """
        query = self.db.query(Team).filter(Team.id == team_id)
        query = query.options(joinedload(Team.owner))
        if with_members:
            query = query.options(
                joinedload(Team.members).joinedload(TeamMember.user),
                joinedload(Team.members).joinedload(TeamMember.role),
            )
        return query.first()

    def get_user_teams(self, user_id: str) -> list[Team]:
        """Get all teams for a user (owned or member of).

        Args:
            user_id: User ID

        Returns:
            List of teams
        """
        # Get teams where user is owner or member
        owned_teams = (
            self.db.query(Team)
            .filter(Team.owner_id == user_id)
            .options(joinedload(Team.owner))
            .all()
        )

        member_teams = (
            self.db.query(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .filter(TeamMember.user_id == user_id)
            .options(joinedload(Team.owner))
            .all()
        )

        # Combine and deduplicate
        team_ids = set()
        teams = []
        for team in owned_teams + member_teams:
            if team.id not in team_ids:
                team_ids.add(team.id)
                teams.append(team)

        return teams

    def get_member_count(self, team_id: str) -> int:
        """Get count of members in a team.

        Args:
            team_id: Team ID

        Returns:
            Number of members
        """
        return (
            self.db.query(func.count(TeamMember.user_id))
            .filter(TeamMember.team_id == team_id)
            .scalar()
            or 0
        )

    def create(self, team_data: TeamCreate, owner_id: str) -> Team:
        """Create a new team.

        Args:
            team_data: Team creation data
            owner_id: Owner user ID

        Returns:
            Created team
        """
        team = Team(
            id=generate_cuid(),
            name=team_data.name,
            description=team_data.description,
            owner_id=owner_id,
        )

        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)

        # Reload with owner
        return self.get_by_id(team.id)

    def update(self, team_id: str, team_data: TeamUpdate) -> Team | None:
        """Update team.

        Args:
            team_id: Team ID
            team_data: Team update data

        Returns:
            Updated team or None if not found
        """
        team = self.get_by_id(team_id)
        if not team:
            return None

        update_dict = team_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(team, key, value)

        self.db.commit()
        self.db.refresh(team)

        return team

    def delete(self, team_id: str) -> bool:
        """Delete team.

        Args:
            team_id: Team ID

        Returns:
            True if deleted, False if not found
        """
        team = self.get_by_id(team_id)
        if not team:
            return False

        self.db.delete(team)
        self.db.commit()

        return True

    def add_member(
        self, team_id: str, user_id: str, role_id: str | None = None
    ) -> TeamMember | None:
        """Add a member to a team.

        Args:
            team_id: Team ID
            user_id: User ID to add
            role_id: Optional role ID for the member

        Returns:
            Created TeamMember or None if team/user not found
        """
        team = self.get_by_id(team_id)
        if not team:
            return None

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Check if already a member
        existing = (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        if existing:
            # Update role if provided
            if role_id is not None:
                existing.role_id = role_id
                self.db.commit()
            return existing

        member = TeamMember(team_id=team_id, user_id=user_id, role_id=role_id)

        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return member

    def remove_member(self, team_id: str, user_id: str) -> bool:
        """Remove a member from a team.

        Args:
            team_id: Team ID
            user_id: User ID to remove

        Returns:
            True if removed, False if not found
        """
        member = (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )

        if not member:
            return False

        self.db.delete(member)
        self.db.commit()

        return True

    def is_owner(self, team_id: str, user_id: str) -> bool:
        """Check if user is the owner of a team.

        Args:
            team_id: Team ID
            user_id: User ID

        Returns:
            True if user is owner
        """
        team = self.get_by_id(team_id)
        return team is not None and team.owner_id == user_id

    def is_member(self, team_id: str, user_id: str) -> bool:
        """Check if user is a member of a team.

        Args:
            team_id: Team ID
            user_id: User ID

        Returns:
            True if user is member
        """
        member = (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        return member is not None
