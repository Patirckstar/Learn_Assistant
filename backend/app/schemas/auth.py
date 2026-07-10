from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, description="用户名")
    password: str = Field(min_length=6, description="密码")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str


class UserInfoResponse(BaseModel):
    id: int
    username: str
    face_encoding: str | None
    face_image_path: str | None
    created_at: str


class FaceImageRequest(BaseModel):
    image_data: str
