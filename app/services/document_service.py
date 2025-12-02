"""Document service for business logic."""

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import Document, DocumentShare, DocumentTag, Tag
from app.models.base import generate_cuid
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentService:
    """Document service for managing document operations."""

    def __init__(self, db: Session) -> None:
        """Initialize document service.

        Args:
            db: Database session
        """
        self.db = db

    def get_by_id(self, document_id: str, with_relations: bool = True) -> Document | None:
        """Get document by ID.

        Args:
            document_id: Document ID
            with_relations: Whether to eager load relations

        Returns:
            Document or None if not found
        """
        query = self.db.query(Document).filter(Document.id == document_id)
        if with_relations:
            query = query.options(
                joinedload(Document.owner),
                joinedload(Document.tags).joinedload(DocumentTag.tag),
            )
        return query.first()

    def get_list(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 10,
        folder_id: str | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
    ) -> tuple[list[Document], int]:
        """Get paginated document list.

        Args:
            user_id: User ID (owner or shared with)
            page: Page number
            limit: Items per page
            folder_id: Filter by folder
            tags: Filter by tags
            search: Search in title

        Returns:
            Tuple of (documents, total_count)
        """
        query = self.db.query(Document).options(
            joinedload(Document.owner),
            joinedload(Document.tags).joinedload(DocumentTag.tag),
        )

        # Filter by owner or shared with user
        query = query.filter(
            or_(
                Document.owner_id == user_id,
                Document.id.in_(
                    self.db.query(DocumentShare.document_id).filter(
                        DocumentShare.shared_with_id == user_id
                    )
                ),
            )
        )

        # Filter by folder
        if folder_id:
            query = query.filter(Document.folder == folder_id)

        # Filter by tags
        if tags:
            tag_ids = self.db.query(Tag.id).filter(Tag.name.in_(tags)).subquery()
            query = query.filter(
                Document.id.in_(
                    self.db.query(DocumentTag.document_id).filter(DocumentTag.tag_id.in_(tag_ids))
                )
            )

        # Search in title
        if search:
            query = query.filter(Document.title.ilike(f"%{search}%"))

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        documents = query.order_by(Document.updated_at.desc()).offset(offset).limit(limit).all()

        return documents, total

    def create(
        self,
        document_data: DocumentCreate,
        owner_id: str,
    ) -> Document:
        """Create a new document.

        Args:
            document_data: Document creation data
            owner_id: Owner user ID

        Returns:
            Created document
        """
        document = Document(
            id=generate_cuid(),
            title=document_data.title,
            content=document_data.content,
            folder=document_data.folderId,
            type="document",
            size=len(document_data.content.encode("utf-8")),
            owner_id=owner_id,
        )

        self.db.add(document)
        self.db.flush()

        # Add tags
        if document_data.tags:
            self._update_tags(document.id, document_data.tags)

        self.db.commit()
        self.db.refresh(document)

        return self.get_by_id(document.id)

    def update(self, document_id: str, document_data: DocumentUpdate) -> Document | None:
        """Update document.

        Args:
            document_id: Document ID
            document_data: Document update data

        Returns:
            Updated document or None if not found
        """
        document = self.get_by_id(document_id, with_relations=False)
        if not document:
            return None

        update_dict = document_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(document, key, value)

        # Update size if content changed
        if "content" in update_dict:
            document.size = len(document.content.encode("utf-8"))

        self.db.commit()
        self.db.refresh(document)

        return self.get_by_id(document_id)

    def rename(self, document_id: str, title: str) -> Document | None:
        """Rename document.

        Args:
            document_id: Document ID
            title: New title

        Returns:
            Updated document or None if not found
        """
        document = self.get_by_id(document_id, with_relations=False)
        if not document:
            return None

        document.title = title
        self.db.commit()

        return self.get_by_id(document_id)

    def move(self, document_id: str, folder_id: str | None) -> Document | None:
        """Move document to folder.

        Args:
            document_id: Document ID
            folder_id: Target folder ID (None for root)

        Returns:
            Updated document or None if not found
        """
        document = self.get_by_id(document_id, with_relations=False)
        if not document:
            return None

        document.folder = folder_id
        self.db.commit()

        return self.get_by_id(document_id)

    def update_tags(self, document_id: str, tags: list[str]) -> Document | None:
        """Update document tags.

        Args:
            document_id: Document ID
            tags: List of tag names

        Returns:
            Updated document or None if not found
        """
        document = self.get_by_id(document_id, with_relations=False)
        if not document:
            return None

        self._update_tags(document_id, tags)
        self.db.commit()

        return self.get_by_id(document_id)

    def _update_tags(self, document_id: str, tag_names: list[str]) -> None:
        """Update tags for a document (internal helper).

        Args:
            document_id: Document ID
            tag_names: List of tag names
        """
        # Remove existing tags
        self.db.query(DocumentTag).filter(DocumentTag.document_id == document_id).delete(
            synchronize_session=False
        )

        # Add new tags
        for tag_name in tag_names:
            # Get or create tag
            tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(id=generate_cuid(), name=tag_name)
                self.db.add(tag)
                self.db.flush()

            # Create document-tag relation
            doc_tag = DocumentTag(document_id=document_id, tag_id=tag.id)
            self.db.add(doc_tag)

    def share(
        self,
        document_id: str,
        user_id: str | None = None,
        team_id: str | None = None,
        permission: str = "READ",
    ) -> DocumentShare | None:
        """Share document with user or team.

        Args:
            document_id: Document ID
            user_id: User ID to share with
            team_id: Team ID to share with
            permission: Permission level

        Returns:
            Created share or None if document not found
        """
        document = self.get_by_id(document_id, with_relations=False)
        if not document:
            return None

        # Check if already shared - build filters dynamically
        filters = [DocumentShare.document_id == document_id]
        if user_id:
            filters.append(DocumentShare.shared_with_id == user_id)
        if team_id:
            filters.append(DocumentShare.team_id == team_id)

        existing = self.db.query(DocumentShare).filter(*filters).first()

        if existing:
            existing.permission = permission
            self.db.commit()
            return existing

        share = DocumentShare(
            id=generate_cuid(),
            document_id=document_id,
            shared_with_id=user_id,
            team_id=team_id,
            permission=permission,
        )

        self.db.add(share)
        self.db.commit()
        self.db.refresh(share)

        return share

    def unshare(
        self,
        document_id: str,
        user_id: str | None = None,
        team_id: str | None = None,
    ) -> bool:
        """Remove share from document.

        Args:
            document_id: Document ID
            user_id: User ID to unshare
            team_id: Team ID to unshare

        Returns:
            True if unshared, False if not found
        """
        query = self.db.query(DocumentShare).filter(DocumentShare.document_id == document_id)

        if user_id:
            query = query.filter(DocumentShare.shared_with_id == user_id)
        if team_id:
            query = query.filter(DocumentShare.team_id == team_id)

        deleted = query.delete(synchronize_session=False)
        self.db.commit()

        return deleted > 0

    def delete(self, document_id: str) -> bool:
        """Delete document.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        document = self.get_by_id(document_id, with_relations=False)
        if not document:
            return False

        self.db.delete(document)
        self.db.commit()

        return True

    def batch_delete(self, document_ids: list[str], user_id: str) -> int:
        """Batch delete documents.

        Args:
            document_ids: List of document IDs
            user_id: User ID (must be owner)

        Returns:
            Number of deleted documents
        """
        deleted = (
            self.db.query(Document)
            .filter(Document.id.in_(document_ids), Document.owner_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()

        return deleted

    def is_owner(self, document_id: str, user_id: str) -> bool:
        """Check if user is owner of document.

        Args:
            document_id: Document ID
            user_id: User ID

        Returns:
            True if user is owner
        """
        document = self.get_by_id(document_id, with_relations=False)
        return document is not None and document.owner_id == user_id

    def can_access(self, document_id: str, user_id: str) -> bool:
        """Check if user can access document.

        Args:
            document_id: Document ID
            user_id: User ID

        Returns:
            True if user can access
        """
        document = self.get_by_id(document_id, with_relations=False)
        if not document:
            return False

        if document.owner_id == user_id:
            return True

        # Check if shared with user directly
        share = (
            self.db.query(DocumentShare)
            .filter(
                DocumentShare.document_id == document_id,
                DocumentShare.shared_with_id == user_id,
            )
            .first()
        )

        if share:
            return True

        # Check if shared via team membership
        from app.models import TeamMember

        team_share = (
            self.db.query(DocumentShare)
            .filter(
                DocumentShare.document_id == document_id,
                DocumentShare.team_id.in_(
                    self.db.query(TeamMember.team_id).filter(TeamMember.user_id == user_id)
                ),
            )
            .first()
        )

        return team_share is not None
