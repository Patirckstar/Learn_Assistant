import request from '@/api/request'

export interface ProfileInfo {
  id: number
  user_id: number
  username: string
  nickname: string | null
  avatar_path: string | null
  email: string | null
  phone: string | null
  bio: string | null
  face_encoding: string | null
  face_image_path: string | null
  created_at: string
  updated_at: string | null
}

export interface ProfileUpdate {
  nickname: string | null
  email: string | null
  phone: string | null
  bio: string | null
}

export function getProfile() {
  return request.get<ProfileInfo>('/api/profile')
}

export function updateProfile(data: ProfileUpdate) {
  return request.put<ProfileInfo>('/api/profile', data)
}
