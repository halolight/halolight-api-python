"""Folder management routes matching API spec."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models import Folder, User
from app.models.base import generate_cuid
from app.schemas.user import UserBasicResponse

router = APIRouter(prefix="/folders", tags=["Folders"])


# ============== Schemas ==============
class FolderCreate(BaseModel):
    name: str
    parentId: str | None = None


class FolderUpdate(BaseModel):
    name: str | None = None


class FolderResponse(BaseModel):
    id: str
    name: str
    parentId: str | None = None
    owner: UserBasicResponse
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FolderTreeNode(BaseModel):
    id: str
    name: str
    children: list["FolderTreeNode"] = Field(default_factory=list)


class FolderListResponse(BaseModel):
    data: list[FolderResponse]


class FolderTreeResponse(BaseModel):
    data: list[FolderTreeNode]


# ============== Helper ==============
def _build_folder_response(folder: Folder) -> FolderResponse:
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parentId=folder.parent_id,
        owner=UserBasicResponse(
            id=folder.owner.id,
            email=folder.owner.email,
            name=folder.owner.name,
            avatar=folder.owner.avatar,
        ),
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )


def _build_folder_tree(folders: list[Folder], parent_id: str | None = None) -> list[FolderTreeNode]:
    """Build folder tree recursively."""
    nodes = []
    for folder in folders:
        if folder.parent_id == parent_id:
            children = _build_folder_tree(folders, folder.id)
            nodes.append(FolderTreeNode(id=folder.id, name=folder.name, children=children))
    return nodes


# ============== Routes ==============
@router.get("", response_model=FolderListResponse)
async def list_folders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FolderListResponse:
    """Get all folders for current user."""
    folders = (
        db.query(Folder)
        .filter(Folder.owner_id == current_user.id)
        .options(joinedload(Folder.owner))
        .order_by(Folder.name)
        .all()
    )

    return FolderListResponse(data=[_build_folder_response(f) for f in folders])


@router.get("/tree", response_model=FolderTreeResponse)
async def get_folder_tree(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FolderTreeResponse:
    """Get folder tree structure."""
    folders = db.query(Folder).filter(Folder.owner_id == current_user.id).all()
    tree = _build_folder_tree(folders)

    return FolderTreeResponse(data=tree)


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FolderResponse:
    """Get folder by ID."""
    folder = (
        db.query(Folder)
        .filter(Folder.id == folder_id, Folder.owner_id == current_user.id)
        .options(joinedload(Folder.owner))
        .first()
    )

    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    return _build_folder_response(folder)


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FolderResponse:
    """Create a new folder."""
    # Validate parent folder if provided and build path
    parent_path = ""
    if folder_data.parentId:
        parent = (
            db.query(Folder)
            .filter(Folder.id == folder_data.parentId, Folder.owner_id == current_user.id)
            .first()
        )
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent folder not found"
            )
        parent_path = parent.path

    # Generate unique path
    folder_id = generate_cuid()
    folder_path = f"{parent_path}/{folder_data.name}" if parent_path else f"/{folder_data.name}"

    folder = Folder(
        id=folder_id,
        name=folder_data.name,
        path=folder_path,
        parent_id=folder_data.parentId,
        owner_id=current_user.id,
    )

    db.add(folder)
    db.commit()
    db.refresh(folder)

    folder = (
        db.query(Folder).filter(Folder.id == folder.id).options(joinedload(Folder.owner)).first()
    )
    return _build_folder_response(folder)


@router.patch("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: str,
    folder_data: FolderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FolderResponse:
    """Update folder."""
    folder = (
        db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == current_user.id).first()
    )

    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    if folder_data.name:
        folder.name = folder_data.name

    db.commit()

    folder = (
        db.query(Folder).filter(Folder.id == folder.id).options(joinedload(Folder.owner)).first()
    )
    return _build_folder_response(folder)


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Delete folder."""
    folder = (
        db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == current_user.id).first()
    )

    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    db.delete(folder)
    db.commit()

    return {"message": "Folder successfully deleted", "id": folder_id}
