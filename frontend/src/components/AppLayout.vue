<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-left">
        <span class="app-logo">健康趋势分析</span>
      </div>

      <div class="header-right">
        <el-select
          v-model="authStore.currentPatient"
          value-key="id"
          placeholder="选择患者"
          size="small"
          class="patient-select"
          :teleported="false"
          fit-input-width
        >
          <template #prefix>
            <el-icon><User /></el-icon>
          </template>
          <el-option
            v-for="p in authStore.patients"
            :key="p.id"
            :label="p.name"
            :value="p"
          />
        </el-select>
        <el-dropdown trigger="click">
          <el-avatar :size="32" style="background:var(--primary);cursor:pointer;font-size:14px;">
            {{ userInitial }}
          </el-avatar>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                <span style="color:var(--text-secondary);font-size:12px">{{ authStore.user?.username }}</span>
              </el-dropdown-item>
              <el-dropdown-item divided @click="navigate('/patients')">
                <el-icon><User /></el-icon> 患者管理
              </el-dropdown-item>
              <el-dropdown-item divided @click="doLogout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>

    <!-- 底部 TabBar -->
    <nav class="tabbar" v-if="isMobile">
      <div
        v-for="item in tabItems"
        :key="item.path"
        class="tab-item"
        :class="{ active: isActive(item.path) }"
        @click="navigate(item.path)"
      >
        <el-icon :size="22"><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </div>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  DataBoard, EditPen, TrendCharts, Document,
  User, SwitchButton, Collection, Timer, SetUp
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const isMobile = ref(false)

const userInitial = computed(() => {
  const name = authStore.user?.username || 'U'
  return name.charAt(0).toUpperCase()
})

const tabItems = [
  { path: '/reports', label: '报告', icon: Document },
  { path: '/trend', label: '趋势', icon: TrendCharts },
  { path: '/entry', label: '录入', icon: EditPen },
  { path: '/dashboard', label: '首页', icon: DataBoard },
  { path: '/medications', label: '用药', icon: Collection },
  { path: '/templates', label: '模板', icon: SetUp },
  { path: '/med-timeline', label: '周期', icon: Timer },
]

function isActive(path: string) {
  return route.path.startsWith(path)
}

function navigate(path: string) {
  router.push(path)
}

function doLogout() {
  authStore.clearToken()
  router.push('/login')
}

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  if (!authStore.currentPatient) await authStore.loadPatients()
  if (!authStore.user) await authStore.loadUser()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: var(--bg);
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 52px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  gap: 12px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.app-logo {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-color-adjust: exact;
  color: transparent;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  margin-left: auto;
}

.patient-select {
  width: 110px;
}

.patient-select :deep(.el-input__wrapper) {
  border-radius: 20px;
  background: #f5f7ff;
  box-shadow: none;
}

.patient-select :deep(.el-input__inner) {
  font-size: 13px;
}

.app-main {
  min-height: calc(100vh - 52px);
}

/* 底部 TabBar */
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(56px + constant(safe-area-inset-bottom));
  height: calc(56px + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-around;
  align-items: flex-start;
  padding-top: 4px;
  z-index: 100;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.05);
}

.tab-item {
  flex: 1;
  max-width: 90px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6px 4px 8px;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  gap: 4px;
  -webkit-tap-highlight-color: transparent;
}

.tab-item:active {
  transform: scale(0.92);
}

.tab-item.active {
  color: #667eea;
}

.tab-item .el-icon {
  transition: transform 0.2s;
}

.tab-item.active .el-icon {
  transform: scale(1.15);
}

/* 桌面端隐藏 TabBar */
@media (min-width: 769px) {
  .tabbar {
    display: none;
  }
  
  .app-header {
    padding: 0 24px;
  }
  
  .patient-select {
    width: 130px;
  }
}
</style>
