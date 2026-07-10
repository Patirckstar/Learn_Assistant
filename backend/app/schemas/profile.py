from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    nickname: str | None = Field(None, max_length=100, description="昵称")
    email: str | None = Field(None, max_length=255, description="电子邮箱")
    phone: str | None = Field(None, max_length=20, description="手机号")
    bio: str | None = Field(None, description="个人简介")


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    username: str
    nickname: str | None
    avatar_path: str | None
    email: str | None
    phone: str | None
    bio: str | None
    face_encoding: str | None
    face_image_path: str | None
    created_at: str
    updated_at: str | None
