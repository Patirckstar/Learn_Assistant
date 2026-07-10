from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/api/profile", tags=["个人信息"])


def _get_or_create_profile(db: Session, user: User) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    profile = _get_or_create_profile(db, current_user)
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        username=current_user.username,
        nickname=profile.nickname,
        avatar_path=profile.avatar_path,
        email=profile.email,
        phone=profile.phone,
        bio=profile.bio,
        face_encoding=current_user.face_encoding,
        face_image_path=current_user.face_image_path,
        created_at=str(current_user.created_at),
        updated_at=str(profile.updated_at) if profile.updated_at else None,
    )


@router.put("", response_model=ProfileResponse)
def update_profile(
    data: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    profile = _get_or_create_profile(db, current_user)

    if data.nickname is not None:
        profile.nickname = data.nickname
    if data.email is not None:
        profile.email = data.email
    if data.phone is not None:
        profile.phone = data.phone
    if data.bio is not None:
        profile.bio = data.bio

    db.commit()
    db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        username=current_user.username,
        nickname=profile.nickname,
        avatar_path=profile.avatar_path,
        email=profile.email,
        phone=profile.phone,
        bio=profile.bio,
        face_encoding=current_user.face_encoding,
        face_image_path=current_user.face_image_path,
        created_at=str(current_user.created_at),
        updated_at=str(profile.updated_at) if profile.updated_at else None,
    )
