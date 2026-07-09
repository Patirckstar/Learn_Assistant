<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
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
      </el-menu>

      <div class="sidebar-footer">
        <div class="sidebar-footer-text">Learn Assistant v1.0</div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Document, Reading, EditPen, DataBoard, Notebook } from '@element-plus/icons-vue'
const route = useRoute()
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

/* 侧边栏 */
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

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
}

.sidebar-footer-text {
  font-size: 11px;
  color: var(--color-text-secondary);
  letter-spacing: 0.5px;
}

/* 主内容区 */
.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 32px 40px;
  min-height: 100vh;
  max-width: 1200px;
}
</style>
