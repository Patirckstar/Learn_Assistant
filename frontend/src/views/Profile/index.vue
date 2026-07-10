<template>
  <div class="profile-page">
    <div class="profile-header">
      <h1>个人中心</h1>
      <p class="subtitle">管理您的个人信息和人脸识别设置</p>
    </div>

    <div class="profile-content">
      <!-- 账号信息卡片 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><User /></el-icon>
            <span>账号信息</span>
          </div>
        </template>
        <div class="info-list">
          <div class="info-item">
            <span class="label">用户名</span>
            <span class="value">{{ authStore.user?.username || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">用户ID</span>
            <span class="value">{{ authStore.user?.id || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">注册时间</span>
            <span class="value">{{ formatDateTime(authStore.user?.created_at) }}</span>
          </div>
          <div class="info-item">
            <span class="label">人脸状态</span>
            <span class="value">
              <el-tag :type="faceRegistered ? 'success' : 'warning'" size="small">
                {{ faceRegistered ? '已录入' : '未录入' }}
              </el-tag>
            </span>
          </div>
        </div>
      </el-card>

      <!-- 个人资料编辑卡片 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><EditPen /></el-icon>
            <span>个人资料</span>
          </div>
        </template>
        <el-form :model="profileForm" label-position="top" class="profile-form">
          <el-form-item label="昵称">
            <el-input v-model="profileForm.nickname" placeholder="请输入昵称" maxlength="100" show-word-limit />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="profileForm.email" placeholder="请输入邮箱" maxlength="255" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="profileForm.phone" placeholder="请输入手机号" maxlength="20" />
          </el-form-item>
          <el-form-item label="个人简介">
            <el-input v-model="profileForm.bio" type="textarea" :rows="3" placeholder="介绍一下自己..." maxlength="500" show-word-limit />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="handleSaveProfile">
              保存资料
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 人脸识别设置卡片 -->
      <el-card class="face-card">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><Camera /></el-icon>
            <span>人脸识别设置</span>
          </div>
        </template>

        <div class="face-content">
          <p class="face-description">
            注册人脸后，您可以使用人脸识别快速登录系统。请确保光线充足，正对摄像头拍摄清晰人脸照片。
          </p>

          <!-- 已录入 -->
          <template v-if="faceRegistered">
            <el-alert type="success" :closable="false" class="face-success-alert">
              <template #title>
                <el-icon><CircleCheck /></el-icon>
                人脸已录入，您可以使用人脸识别登录
              </template>
            </el-alert>
            <div class="face-placeholder">
              <el-button type="warning" plain @click="openFaceDialog">
                <el-icon><Refresh /></el-icon>
                重新录入人脸
              </el-button>
            </div>
          </template>

          <!-- 未录入 -->
          <template v-else>
            <div class="face-placeholder">
              <el-button type="primary" @click="openFaceDialog">
                <el-icon><VideoCamera /></el-icon>
                录入人脸
              </el-button>
            </div>
          </template>
        </div>
      </el-card>

      <!-- 账户操作卡片 -->
      <el-card class="action-card">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><Setting /></el-icon>
            <span>账户操作</span>
          </div>
        </template>
        <div class="action-content">
          <el-button type="danger" plain @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 人脸录入弹窗 -->
    <el-dialog
      v-model="faceDialogVisible"
      title="人脸录入"
      width="520px"
      :close-on-click-modal="false"
      @close="closeFaceDialog"
      destroy-on-close
    >
      <div class="face-dialog-content">
        <p class="face-dialog-tip">请正对摄像头，确保光线充足、面部清晰可见</p>

        <div class="dialog-camera-container">
          <video ref="videoRef" autoplay playsinline class="camera-video"></video>
          <canvas ref="canvasRef" class="camera-canvas"></canvas>
          <div v-if="!cameraStarted" class="camera-placeholder">
            <el-icon class="placeholder-icon"><VideoCamera /></el-icon>
            <p>点击下方按钮开启摄像头</p>
          </div>
          <div v-if="faceDetecting" class="detect-overlay">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <p>正在识别...</p>
          </div>
        </div>

        <div class="dialog-camera-actions">
          <el-button
            :type="cameraStarted ? 'default' : 'primary'"
            :loading="cameraLoading"
            @click="toggleCamera"
            :disabled="faceDetecting"
          >
            {{ cameraStarted ? '关闭摄像头' : '开启摄像头' }}
          </el-button>
          <el-button
            type="success"
            :loading="registering"
            @click="handleRegisterFace"
            :disabled="!cameraStarted || faceDetecting"
          >
            拍照并录入
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, onActivated, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, EditPen, Camera, VideoCamera, Loading, CircleCheck, Setting, SwitchButton, Refresh } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

defineOptions({ name: 'Profile' })

const router = useRouter()
const authStore = useAuthStore()

const saving = ref(false)
const registering = ref(false)
const cameraStarted = ref(false)
const cameraLoading = ref(false)
const faceDetecting = ref(false)
const faceDialogVisible = ref(false)

const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const profileForm = reactive({
  nickname: '',
  email: '',
  phone: '',
  bio: '',
})

const faceRegistered = computed(() => !!authStore.user?.face_encoding)

let mediaStream: MediaStream | null = null

function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

async function handleSaveProfile() {
  saving.value = true
  try {
    await authStore.saveProfile({
      nickname: profileForm.nickname || null,
      email: profileForm.email || null,
      phone: profileForm.phone || null,
      bio: profileForm.bio || null,
    })
    ElMessage.success('个人资料已保存')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function openFaceDialog() {
  faceDialogVisible.value = true
  await nextTick()
  await toggleCamera()
}

async function toggleCamera() {
  if (cameraStarted.value) {
    stopCamera()
    return
  }
  cameraLoading.value = true
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user' },
      audio: false,
    })
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      videoRef.value.play()
      cameraStarted.value = true
    }
  } catch (e: any) {
    if (e.name === 'NotAllowedError') {
      ElMessage.error('摄像头权限被拒绝，请在浏览器设置中允许摄像头访问')
    } else if (e.name === 'NotFoundError') {
      ElMessage.error('未检测到摄像头设备')
    } else {
      ElMessage.error('无法访问摄像头: ' + (e.message || '未知错误'))
    }
  } finally {
    cameraLoading.value = false
  }
}

function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop())
    mediaStream = null
  }
  cameraStarted.value = false
}

function captureImage(): string {
  if (!videoRef.value || !canvasRef.value) return ''
  const canvas = canvasRef.value
  canvas.width = videoRef.value.videoWidth
  canvas.height = videoRef.value.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return ''
  ctx.drawImage(videoRef.value, 0, 0)
  return canvas.toDataURL('image/jpeg', 0.8)
}

async function handleRegisterFace() {
  faceDetecting.value = true
  registering.value = true
  try {
    const imageData = captureImage()
    if (!imageData) {
      ElMessage.error('无法捕获图像')
      return
    }
    await authStore.registerFace(imageData)
    ElMessage.success('人脸录入成功')
    faceDialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e.message || '人脸录入失败')
  } finally {
    faceDetecting.value = false
    registering.value = false
  }
}

function closeFaceDialog() {
  stopCamera()
}

function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

function loadProfileData() {
  if (authStore.isLoggedIn()) {
    authStore.fetchUserInfo()
    authStore.fetchProfile()
  }
}

watch(
  () => authStore.profile,
  (p) => {
    if (p) {
      profileForm.nickname = p.nickname || ''
      profileForm.email = p.email || ''
      profileForm.phone = p.phone || ''
      profileForm.bio = p.bio || ''
    }
  },
  { immediate: true },
)

onMounted(loadProfileData)
onActivated(loadProfileData)

onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.profile-page {
  max-width: 800px;
}

.profile-header {
  margin-bottom: 24px;
}

.profile-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-heading);
  margin: 0 0 8px;
}

.subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.profile-content {
  display: grid;
  gap: 20px;
}

.info-card,
.face-card,
.action-card {
  border-radius: var(--radius-md);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-heading);
}

.header-icon {
  font-size: 20px;
  color: var(--color-primary);
}

.info-list {
  display: grid;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border-light);
}

.info-item:last-child {
  border-bottom: none;
}

.label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.value {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.profile-form {
  max-width: 500px;
}

.face-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.face-description {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

.face-success-alert {
  margin: 0;
}

.face-placeholder {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.action-content {
  padding: 8px 0;
}

/* ---- 弹窗内摄像头样式 ---- */
.face-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.face-dialog-tip {
  font-size: 14px;
  color: var(--color-text-secondary);
  text-align: center;
  margin: 0;
}

.dialog-camera-container {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  background: #1f2937;
  border-radius: 8px;
  overflow: hidden;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-canvas {
  display: none;
}

.camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  gap: 12px;
}

.placeholder-icon {
  font-size: 64px;
}

.camera-placeholder p {
  margin: 0;
  font-size: 14px;
}

.detect-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  color: #fbbf24;
}

.loading-icon {
  font-size: 40px;
  margin-bottom: 12px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.detect-overlay p {
  margin: 0;
  font-size: 14px;
}

.dialog-camera-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
