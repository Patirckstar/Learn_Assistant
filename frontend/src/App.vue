<template>
  <div class="app-layout" :class="{ 'no-sidebar': route.path === '/login' }">
    <aside v-show="route.path !== '/login'" class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <span class="brand-text">AI 学习助手</span>
      </div>

      <el-menu
        :default-active="route.path"
        router
        :ellipsis="false"
        class="sidebar-menu"
      >
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/course">
          <el-icon><Reading /></el-icon>
          <span>课程学习</span>
        </el-menu-item>
        <el-menu-item index="/quiz">
          <el-icon><EditPen /></el-icon>
          <span>在线测验</span>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>学习进度</span>
        </el-menu-item>
        <el-menu-item index="/wrongbook">
          <el-icon><Notebook /></el-icon>
          <span>错题本</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-voice">
        <button class="voice-trigger-btn" @click="showVoiceModal = true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
          <span>语音指令</span>
        </button>
      </div>

      <div class="sidebar-voice-toggles">
        <div class="voice-toggle-item" @click="voiceStore.toggleSTT()">
          <svg class="toggle-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          </svg>
          <span>语音输入</span>
          <span class="toggle-switch" :class="{ on: voiceStore.sttEnabled }">
            <span class="toggle-knob"></span>
          </span>
        </div>
        <div class="voice-toggle-item" @click="voiceStore.toggleTTS()">
          <svg class="toggle-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
          </svg>
          <span>语音播报</span>
          <span class="toggle-switch" :class="{ on: voiceStore.ttsEnabled }">
            <span class="toggle-knob"></span>
          </span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="user-info">
          <el-icon class="user-icon"><User /></el-icon>
          <span class="user-name">{{ authStore.user?.username || '未登录' }}</span>
        </div>
        <div class="sidebar-footer-text">Learn Assistant v1.0</div>
      </div>
    </aside>

    <VoiceCommand v-model:visible="showVoiceModal" />

    <main class="main-content" :class="{ 'full-width': route.path === '/login' }">
      <router-view v-slot="{ Component, route: r }">
        <keep-alive>
          <component :is="Component" :key="r.path" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Document, Reading, EditPen, DataBoard, Notebook, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useVoiceStore } from '@/stores/voice'
import VoiceCommand from '@/views/VoiceCommand/index.vue'

const route = useRoute()
const authStore = useAuthStore()
const voiceStore = useVoiceStore()
const showVoiceModal = ref(false)

onMounted(() => {
  if (authStore.isLoggedIn()) {
    authStore.fetchUserInfo()
    authStore.fetchProfile()
  }
})
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.app-layout.no-sidebar {
  display: block;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.brand-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border-radius: var(--radius-sm);
}

.brand-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-heading);
  letter-spacing: -0.3px;
}

.sidebar-menu {
  flex: 1;
  padding: 12px 8px;
  border-right: none !important;
}

.sidebar-menu .el-menu-item {
  border-radius: var(--radius-sm);
  margin: 2px 0;
  font-size: 14px;
  height: 42px;
  line-height: 42px;
}

.sidebar-menu .el-menu-item.is-active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 500;
}

.sidebar-voice {
  padding: 8px 20px;
}

.voice-trigger-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 0;
  border: 1.5px dashed var(--color-border);
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.voice-trigger-btn:hover {
  border-color: var(--color-primary);
  background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 100%);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
  transform: translateY(-1px);
}

.voice-trigger-btn:active {
  transform: translateY(0);
}

.sidebar-voice-toggles {
  padding: 0 20px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.voice-toggle-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  color: var(--color-text-secondary);
  transition: background 0.15s;
  user-select: none;
}

.voice-toggle-item:hover {
  background: var(--color-primary-light);
}

.toggle-icon {
  flex-shrink: 0;
  color: var(--color-text-secondary);
}

.toggle-switch {
  margin-left: auto;
  width: 36px;
  height: 20px;
  border-radius: 10px;
  background: #d1d5db;
  position: relative;
  transition: background 0.2s;
}

.toggle-switch.on {
  background: var(--color-primary);
}

.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s;
}

.toggle-switch.on .toggle-knob {
  transform: translateX(16px);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--color-primary-light);
  border-radius: var(--radius-sm);
}

.user-icon {
  font-size: 18px;
  color: var(--color-primary);
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-primary);
}

.sidebar-footer-text {
  font-size: 11px;
  color: var(--color-text-secondary);
  letter-spacing: 0.5px;
  text-align: center;
}

.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 32px 40px;
  min-height: 100vh;
  max-width: 1200px;
}

.main-content.full-width {
  margin-left: 0;
  max-width: none;
  padding: 0;
}
</style>
