import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'
import { getProfile, updateProfile, type ProfileInfo, type ProfileUpdate } from '@/api/profile'

interface TokenResponse {
  access_token: string
  token_type: string
  user_id: number
  username: string
}

interface UserInfo {
  id: number
  username: string
  face_encoding: string | null
  face_image_path: string | null
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token') || null)
  const user = ref<UserInfo | null>(null)
  const profile = ref<ProfileInfo | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function login(username: string, password: string): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const res = await request.post<TokenResponse>('/api/auth/login', {
        username,
        password,
      })
      token.value = res.data.access_token
      localStorage.setItem('token', res.data.access_token)
      user.value = {
        id: res.data.user_id,
        username: res.data.username,
        face_encoding: null,
        face_image_path: null,
        created_at: '',
      }
      await fetchUserInfo()
      await fetchProfile()
    } catch (e: any) {
      error.value = e?.response?.data?.detail || '登录失败'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, password: string): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const res = await request.post<TokenResponse>('/api/auth/register', {
        username,
        password,
      })
      token.value = res.data.access_token
      localStorage.setItem('token', res.data.access_token)
      user.value = {
        id: res.data.user_id,
        username: res.data.username,
        face_encoding: null,
        face_image_path: null,
        created_at: '',
      }
      await fetchUserInfo()
      await fetchProfile()
    } catch (e: any) {
      error.value = e?.response?.data?.detail || '注册失败'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  async function loginByFace(imageData: string): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const res = await request.post<TokenResponse>('/api/face/login', {
        image_data: imageData,
      })
      token.value = res.data.access_token
      localStorage.setItem('token', res.data.access_token)
      user.value = {
        id: res.data.user_id,
        username: res.data.username,
        face_encoding: null,
        face_image_path: null,
        created_at: '',
      }
      await fetchUserInfo()
      await fetchProfile()
    } catch (e: any) {
      error.value = e?.response?.data?.detail || '人脸登录失败'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  async function registerFace(imageData: string): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      await request.post('/api/face/register', {
        image_data: imageData,
      })
      await fetchUserInfo()
    } catch (e: any) {
      error.value = e?.response?.data?.detail || '人脸注册失败'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  async function fetchUserInfo(): Promise<void> {
    if (!token.value) return
    try {
      const res = await request.get<UserInfo>('/api/auth/me')
      user.value = res.data
    } catch {
      // ignore
    }
  }

  async function fetchProfile(): Promise<void> {
    if (!token.value) return
    try {
      const res = await getProfile()
      profile.value = res.data
    } catch {
      // ignore
    }
  }

  async function saveProfile(data: ProfileUpdate): Promise<void> {
    if (!token.value) return
    loading.value = true
    error.value = ''
    try {
      const res = await updateProfile(data)
      profile.value = res.data
    } catch (e: any) {
      error.value = e?.response?.data?.detail || '保存失败'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  function logout(): void {
    token.value = null
    user.value = null
    profile.value = null
    localStorage.removeItem('token')
  }

  function isLoggedIn(): boolean {
    return !!token.value
  }

  return {
    token,
    user,
    profile,
    loading,
    error,
    login,
    register,
    loginByFace,
    registerFace,
    fetchUserInfo,
    fetchProfile,
    saveProfile,
    logout,
    isLoggedIn,
  }
})
