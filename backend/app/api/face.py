from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import FaceImageRequest, TokenResponse
from app.services.face_svc import (
    calculate_distance,
    decode_base64_image,
    decode_from_json,
    detect_and_encode_face,
    encode_to_json,
    save_face_image,
    simple_liveness_detection,
)

router = APIRouter(prefix="/api/face", tags=["人脸识别"])


@router.post("/register")
def register_face(
    data: FaceImageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        image = decode_base64_image(data.image_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片数据无效",
        )

    if not simple_liveness_detection(image):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="活体检测失败，请确保是真实人脸",
        )

    encoding = detect_and_encode_face(image)
    if encoding is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未检测到人脸，请调整角度重新拍摄",
        )

    face_image_path = save_face_image(image, settings.FACE_STORAGE_DIR)
    encoding_json = encode_to_json(encoding)

    user = db.query(User).filter(User.id == current_user.id).first()
    if user:
        user.face_encoding = encoding_json
        user.face_image_path = face_image_path
        db.commit()

    return {"message": "人脸注册成功"}


@router.post("/login", response_model=TokenResponse)
def login_by_face(
    data: FaceImageRequest,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        image = decode_base64_image(data.image_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片数据无效",
        )

    if not simple_liveness_detection(image):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="活体检测失败，请确保是真实人脸",
        )

    encoding = detect_and_encode_face(image)
    if encoding is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未检测到人脸，请调整角度重新拍摄",
        )

    users_with_face = db.query(User).filter(User.face_encoding.isnot(None)).all()
    if len(users_with_face) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未找到已注册人脸的用户，请先注册",
        )

    matched_user = None
    min_distance = float("inf")
    for user in users_with_face:
        try:
            known_encoding = decode_from_json(user.face_encoding)
            distance = calculate_distance(known_encoding, encoding)
            if distance < settings.FACE_TOLERANCE and distance < min_distance:
                min_distance = distance
                matched_user = user
        except Exception:
            continue

    if matched_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="人脸识别失败，请重试或使用密码登录",
        )

    access_token = create_access_token(data={"user_id": matched_user.id})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=matched_user.id,
        username=matched_user.username,
    )
