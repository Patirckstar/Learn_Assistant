<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="brand-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1>AI 学习助手</h1>
        <p>智能学习，轻松掌握</p>
      </div>

      <el-tabs v-model="activeTab" type="border-card" class="login-tabs">
        <el-tab-pane label="密码登录" name="password">
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-position="top">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="passwordForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="passwordForm.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="authStore.loading" @click="handlePasswordLogin" class="login-btn">
                登录
              </el-button>
            </el-form-item>
            <el-form-item class="register-link">
              <span>还没有账号？</span>
              <el-button link @click="showRegister = true">立即注册</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="人脸登录" name="face">
          <div class="face-login-content">
            <div class="camera-container">
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
              <div v-if="faceDetected" class="detect-success">
                <el-icon class="success-icon"><CircleCheck /></el-icon>
                <p>检测到人脸</p>
              </div>
            </div>
            <div class="face-actions">
              <el-button type="primary" :loading="cameraLoading" @click="toggleCamera" :disabled="faceDetecting">
                {{ cameraStarted ? '关闭摄像头' : '开启摄像头' }}
              </el-button>
              <el-button type="success" :loading="authStore.loading" @click="handleFaceLogin" :disabled="!cameraStarted || faceDetecting">
                人脸登录
              </el-button>
            </div>
            <p class="face-tips">请确保光线充足，正对摄像头</p>
            <p class="face-alternative">人脸识别失败？请使用<a href="#" @click.prevent="activeTab = 'password'">密码登录</a></p>
          </div>
        </el-tab-pane>
      </el-tabs>

      <el-dialog v-model="showRegister" title="用户注册" width="400px">
        <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="registerForm.username" placeholder="请输入用户名（至少3个字符）" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="registerForm.password" type="password" placeholder="请输入密码（至少6个字符）" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showRegister = false">取消</el-button>
          <el-button type="primary" :loading="authStore.loading" @click="handleRegister">注册</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElForm, ElFormItem } from 'element-plus'
import { VideoCamera, Loading, CircleCheck } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('password')
const showRegister = ref(false)
const cameraStarted = ref(false)
const cameraLoading = ref(false)
const faceDetecting = ref(false)
const faceDetected = ref(false)

const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const passwordFormRef = ref<InstanceType<typeof ElForm> | null>(null)
const registerFormRef = ref<InstanceType<typeof ElForm> | null>(null)

const passwordForm = ref({
  username: '',
  password: '',
})

const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
})

const passwordRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_: any, value: string, callback: any) => {
        if (value !== registerForm.value.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

let mediaStream: MediaStream | null = null

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
      videoRef.value.onloadedmetadata = () => {
        videoRef.value?.play()
        cameraStarted.value = true
      }
    }
  } catch (e) {
    ElMessage.error('无法访问摄像头，请检查权限设置')
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
  faceDetected.value = false
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

async function handlePasswordLogin() {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await authStore.login(passwordForm.value.username, passwordForm.value.password)
      ElMessage.success('登录成功')
      router.push('/knowledge')
    } catch (e: any) {
      ElMessage.error(e.message)
    }
  })
}

async function handleFaceLogin() {
  faceDetecting.value = true
  try {
    const imageData = captureImage()
    if (!imageData) {
      ElMessage.error('无法捕获图像')
      return
    }
    await authStore.loginByFace(imageData)
    ElMessage.success('人脸识别登录成功')
    stopCamera()
    router.push('/knowledge')
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    faceDetecting.value = false
  }
}

async function handleRegister() {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await authStore.register(registerForm.value.username, registerForm.value.password)
      ElMessage.success('注册成功')
      showRegister.value = false
      router.push('/knowledge')
    } catch (e: any) {
      ElMessage.error(e.message)
    }
  })
}

onMounted(() => {
  if (authStore.isLoggedIn()) {
    router.push('/knowledge')
  }
})

onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  width: 420px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 32px;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.brand-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border-radius: 12px;
  margin: 0 auto 16px;
}

.login-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
}

.login-header p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.login-tabs {
  --el-tabs-header-height: 48px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.register-link {
  text-align: center;
  margin-bottom: 0;
  font-size: 14px;
  color: #6b7280;
}

.register-link span {
  margin-right: 4px;
}

.face-login-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.camera-container {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #1f2937;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.camera-placeholder p {
  margin: 0;
  font-size: 14px;
}

.detect-overlay,
.detect-success {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
}

.detect-overlay {
  color: #fbbf24;
}

.loading-icon {
  font-size: 48px;
  margin-bottom: 12px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.detect-success {
  background: rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

.success-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.detect-overlay p,
.detect-success p {
  margin: 0;
  font-size: 14px;
}

.face-actions {
  display: flex;
  gap: 12px;
  width: 100%;
  margin-bottom: 12px;
}

.face-actions .el-button {
  flex: 1;
  height: 44px;
}

.face-tips {
  font-size: 12px;
  color: #9ca3af;
  margin: 0 0 8px;
}

.face-alternative {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}

.face-alternative a {
  color: #3b82f6;
  text-decoration: none;
}

.face-alternative a:hover {
  text-decoration: underline;
}
</style>
