"""File management routes matching API spec."""

import math
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import File, User
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


class FileShare(BaseModel):
    userId: str | None = None
    teamId: str | None = None
    permission: str = "READ"


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


@router.post("/{file_id}/share")
async def share_file(
    file_id: str,
    share_data: FileShare,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Share file with user or team."""
    file = db.query(File).filter(File.id == file_id, File.owner_id == current_user.id).first()

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # TODO: Implement file sharing logic
    return {"message": "File shared successfully"}


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
