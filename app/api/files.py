"""File management routes matching API spec."""

import math
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import File, FileAccessLog, FileShare, Team, TeamMember, User
from app.models.base import generate_cuid
from app.schemas.user import PaginationMeta, UserBasicResponse

router = APIRouter(prefix="/files", tags=["Files"])


# ============== Schemas ==============


class FileCreate(BaseModel):
    name: str
    path: str
    mimeType: str
    size: int
    folderId: str | None = None


class FileRename(BaseModel):
    name: str


class FileMove(BaseModel):
    folderId: str | None = None


class FileCopy(BaseModel):
    folderId: str | None = None
    name: str | None = None


class ShareFileData(BaseModel):
    userId: str | None = None
    teamId: str | None = None
    permission: str = Field(default="VIEW", pattern="^(VIEW|READ|DOWNLOAD|EDIT)$")
    expiresInDays: int | None = Field(default=None, ge=1, le=365)
    maxAccessCount: int | None = Field(default=None, ge=1)


class FileShareResponse(BaseModel):
    id: str
    shareToken: str
    shareUrl: str
    permission: str
    expiresAt: datetime | None = None
    accessCount: int
    maxAccessCount: int | None = None
    isRevoked: bool
    createdAt: datetime

    model_config = {"from_attributes": True}


class ShareAccessRequest(BaseModel):
    shareToken: str


class RevokeShareRequest(BaseModel):
    shareId: str


class FileResponse(BaseModel):
    id: str
    name: str
    path: str
    mimeType: str
    size: int
    thumbnail: str | None = None
    folderId: str | None = None
    isFavorite: bool = False
    owner: UserBasicResponse
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    data: list[FileResponse]
    meta: PaginationMeta


class StorageInfo(BaseModel):
    used: int
    total: int
    percentage: float


class BatchDeleteRequest(BaseModel):
    ids: list[str]


class BatchDeleteResponse(BaseModel):
    message: str
    deleted_count: int


# ============== Helper ==============
def _build_file_response(file: File) -> FileResponse:
    return FileResponse(
        id=file.id,
        name=file.name,
        path=file.path,
        mimeType=file.mime_type,
        size=file.size,
        thumbnail=file.thumbnail,
        folderId=file.folder_id,
        isFavorite=file.is_favorite,
        owner=UserBasicResponse(
            id=file.owner.id,
            email=file.owner.email,
            name=file.owner.name,
            avatar=file.owner.avatar,
        ),
        created_at=file.created_at,
        updated_at=file.updated_at,
    )


# ============== Routes ==============
@router.get("", response_model=FileListResponse)
async def list_files(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    folderId: str | None = None,
    type: str | None = None,
) -> FileListResponse:
    """Get paginated file list."""
    query = db.query(File).filter(File.owner_id == current_user.id)
    query = query.options(joinedload(File.owner))

    if folderId:
        query = query.filter(File.folder_id == folderId)
    if type:
        query = query.filter(File.mime_type.ilike(f"%{type}%"))

    total = query.count()
    offset = (page - 1) * limit
    files = query.order_by(File.updated_at.desc()).offset(offset).limit(limit).all()

    return FileListResponse(
        data=[_build_file_response(f) for f in files],
        meta=PaginationMeta(
            total=total,
            page=page,
            limit=limit,
            totalPages=math.ceil(total / limit) if total > 0 else 1,
        ),
    )


@router.get("/storage", response_model=StorageInfo)
async def get_storage(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StorageInfo:
    """Get storage usage information."""
    used = db.query(func.sum(File.size)).filter(File.owner_id == current_user.id).scalar() or 0
    total = 10 * 1024 * 1024 * 1024  # 10GB default quota
    percentage = (used / total) * 100 if total > 0 else 0

    return StorageInfo(used=used, total=total, percentage=round(percentage, 2))


@router.get("/storage-info", response_model=StorageInfo)
async def get_storage_info(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StorageInfo:
    """Get storage information (alias)."""
    return await get_storage(db, current_user)


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FileResponse:
    """Get file by ID."""
    file = (
        db.query(File)
        .filter(File.id == file_id, File.owner_id == current_user.id)
        .options(joinedload(File.owner))
        .first()
    )

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return _build_file_response(file)


@router.get("/{file_id}/download-url")
async def get_download_url(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Generate file download URL."""
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # In production, generate a signed URL based on file path
    download_url = f"/api/files/{file_id}/download"
    return {"url": download_url, "path": file.path, "expiresIn": 3600}


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file_data: FileCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FileResponse:
    """Upload a file (metadata only, actual upload handled separately)."""
    file = File(
        id=generate_cuid(),
        name=file_data.name,
        path=file_data.path,
        mime_type=file_data.mimeType,
        size=file_data.size,
        folder_id=file_data.folderId,
        owner_id=current_user.id,
    )

    db.add(file)
    db.commit()
    db.refresh(file)

    file = db.query(File).filter(File.id == file.id).options(joinedload(File.owner)).first()
    return _build_file_response(file)


@router.patch("/{file_id}/rename", response_model=FileResponse)
async def rename_file(
    file_id: str,
    rename_data: FileRename,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FileResponse:
    """Rename file."""
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file.name = rename_data.name
    db.commit()

    file = db.query(File).filter(File.id == file.id).options(joinedload(File.owner)).first()
    return _build_file_response(file)


@router.post("/{file_id}/move", response_model=FileResponse)
async def move_file(
    file_id: str,
    move_data: FileMove,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FileResponse:
    """Move file to folder."""
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file.folder_id = move_data.folderId
    db.commit()

    file = db.query(File).filter(File.id == file.id).options(joinedload(File.owner)).first()
    return _build_file_response(file)


@router.post("/{file_id}/copy", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def copy_file(
    file_id: str,
    copy_data: FileCopy,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FileResponse:
    """Copy file."""
    original = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()

    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    new_file = File(
        id=generate_cuid(),
        name=copy_data.name or f"{original.name} (copy)",
        path=original.path,
        mime_type=original.mime_type,
        size=original.size,
        thumbnail=original.thumbnail,
        folder_id=copy_data.folderId or original.folder_id,
        owner_id=current_user.id,
    )

    db.add(new_file)
    db.commit()

    new_file = db.query(File).filter(File.id == new_file.id).options(joinedload(File.owner)).first()
    return _build_file_response(new_file)


@router.patch("/{file_id}/favorite", response_model=FileResponse)
async def toggle_favorite(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FileResponse:
    """Toggle file favorite status."""
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file.is_favorite = not file.is_favorite
    db.commit()

    file = db.query(File).filter(File.id == file.id).options(joinedload(File.owner)).first()
    return _build_file_response(file)


@router.post(
    "/{file_id}/share", response_model=FileShareResponse, status_code=status.HTTP_201_CREATED
)
async def share_file(
    file_id: str,
    share_data: ShareFileData,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FileShareResponse:
    """
    Share file with user or team.

    Features:
    - Generate unique share token
    - Set expiration time (optional)
    - Limit access count (optional)
    - Support VIEW, READ, DOWNLOAD, EDIT permissions
    - Validate team membership if sharing with team
    """
    # Verify file ownership
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # Validate share data
    if not share_data.userId and not share_data.teamId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either userId or teamId",
        )

    # Validate user exists
    if share_data.userId:
        target_user = db.query(User).filter(User.id == share_data.userId).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found"
            )

    # Validate team exists and membership
    if share_data.teamId:
        team = db.query(Team).filter(Team.id == share_data.teamId).first()
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        # Verify current user is team member or owner
        is_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == share_data.teamId,
                TeamMember.user_id == current_user.id,
            )
            .first()
            is not None
        )
        is_owner = team.owner_id == current_user.id

        if not is_member and not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a team member to share with this team",
            )

    # Check if share already exists
    existing_share = (
        db.query(FileShare)
        .filter(
            FileShare.file_id == file_id,
            FileShare.shared_with_id == share_data.userId if share_data.userId else False,
            FileShare.team_id == share_data.teamId if share_data.teamId else False,
            ~FileShare.is_revoked,
        )
        .first()
    )

    if existing_share:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File already shared with this user/team",
        )

    # Generate unique share token
    share_token = secrets.token_urlsafe(32)

    # Calculate expiration
    expires_at = None
    if share_data.expiresInDays:
        expires_at = datetime.now(UTC) + timedelta(days=share_data.expiresInDays)

    # Create file share
    file_share = FileShare(
        id=generate_cuid(),
        file_id=file_id,
        shared_with_id=share_data.userId,
        team_id=share_data.teamId,
        permission=share_data.permission,
        share_token=share_token,
        expires_at=expires_at,
        max_access_count=share_data.maxAccessCount,
    )

    db.add(file_share)
    db.commit()
    db.refresh(file_share)

    # Generate share URL
    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/api/files/shared/{share_token}"

    return FileShareResponse(
        id=file_share.id,
        shareToken=file_share.share_token,
        shareUrl=share_url,
        permission=file_share.permission,
        expiresAt=file_share.expires_at,
        accessCount=file_share.access_count,
        maxAccessCount=file_share.max_access_count,
        isRevoked=file_share.is_revoked,
        createdAt=file_share.created_at,
    )


@router.get("/shared/{share_token}", response_model=FileResponse)
async def access_shared_file(
    share_token: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_active_user)] = None,
) -> FileResponse:
    """
    Access file via share token.

    Features:
    - Validate share token
    - Check expiration
    - Check access count limits
    - Log access
    - Verify permissions
    """
    # Find share by token
    file_share = (
        db.query(FileShare)
        .filter(FileShare.share_token == share_token, ~FileShare.is_revoked)
        .options(joinedload(FileShare.file).joinedload(File.owner))
        .first()
    )

    if not file_share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found or revoked"
        )

    # Check expiration
    if file_share.expires_at and file_share.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Share link expired")

    # Check access count limit
    if file_share.max_access_count and file_share.access_count >= file_share.max_access_count:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access limit reached")

    # Validate team membership if shared with team
    if file_share.team_id and current_user:
        is_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == file_share.team_id,
                TeamMember.user_id == current_user.id,
            )
            .first()
            is not None
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a team member to access this file",
            )

    # Validate user access if shared with specific user
    if file_share.shared_with_id and current_user:
        if file_share.shared_with_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This file is not shared with you",
            )

    # Increment access count
    file_share.access_count += 1
    db.commit()

    # Log access
    access_log = FileAccessLog(
        id=generate_cuid(),
        file_id=file_share.file_id,
        share_id=file_share.id,
        user_id=current_user.id if current_user else None,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        action="view",
    )
    db.add(access_log)
    db.commit()

    return _build_file_response(file_share.file)


@router.get("/{file_id}/shares", response_model=list[FileShareResponse])
async def list_file_shares(
    file_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[FileShareResponse]:
    """List all shares for a file (owner only)."""
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    shares = db.query(FileShare).filter(FileShare.file_id == file_id).all()

    base_url = str(request.base_url).rstrip("/")
    return [
        FileShareResponse(
            id=share.id,
            shareToken=share.share_token,
            shareUrl=f"{base_url}/api/files/shared/{share.share_token}",
            permission=share.permission,
            expiresAt=share.expires_at,
            accessCount=share.access_count,
            maxAccessCount=share.max_access_count,
            isRevoked=share.is_revoked,
            createdAt=share.created_at,
        )
        for share in shares
    ]


@router.post("/{file_id}/revoke-share")
async def revoke_share(
    file_id: str,
    revoke_data: RevokeShareRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Revoke a file share (owner only)."""
    # Verify file ownership
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # Find and revoke share
    file_share = (
        db.query(FileShare)
        .filter(FileShare.id == revoke_data.shareId, FileShare.file_id == file_id)
        .first()
    )

    if not file_share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")

    file_share.is_revoked = True
    db.commit()

    return {"message": "Share revoked successfully", "shareId": revoke_data.shareId}


@router.get("/{file_id}/access-logs")
async def get_file_access_logs(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Get access logs for a file (owner only)."""
    # Verify file ownership
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    query = db.query(FileAccessLog).filter(FileAccessLog.file_id == file_id)
    total = query.count()
    offset = (page - 1) * limit

    logs = query.order_by(FileAccessLog.accessed_at.desc()).offset(offset).limit(limit).all()

    return {
        "data": [
            {
                "id": log.id,
                "action": log.action,
                "userId": log.user_id,
                "ipAddress": log.ip_address,
                "userAgent": log.user_agent,
                "accessedAt": log.accessed_at,
            }
            for log in logs
        ],
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": math.ceil(total / limit) if total > 0 else 1,
        },
    }


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_files(
    delete_data: BatchDeleteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> BatchDeleteResponse:
    """Batch delete files."""
    deleted = (
        db.query(File)
        .filter(File.id.in_(delete_data.ids), File.owner_id == current_user.id)
        .delete(synchronize_session=False)
    )
    db.commit()

    return BatchDeleteResponse(
        message=f"Successfully deleted {deleted} files",
        deleted_count=deleted,
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete file."""
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    db.delete(file)
    db.commit()

    return {"message": "File successfully deleted", "id": file_id}
