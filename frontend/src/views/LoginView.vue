<template>
  <div class="login-page" @mousemove="onMouseMove">
    <div class="login-bg">
      <div class="bg-circle c1"></div>
      <div class="bg-circle c2"></div>
      <div class="bg-circle c3"></div>
    </div>

    <div class="login-card-wrapper">
      <div class="creature" ref="creatureRef">
        <div class="body">
          <div class="ear ear-left"></div>
          <div class="ear ear-right"></div>
          <div class="face">
            <div class="eye eye-left" :class="{ closed: isPasswordFocused }">
              <div class="eyeball" ref="eyeballLeft"></div>
            </div>
            <div class="eye eye-right" :class="{ closed: isPasswordFocused }">
              <div class="eyeball" ref="eyeballRight"></div>
            </div>
            <div class="nose"></div>
            <div class="mouth" :class="{ smile: tab === 'login' }"></div>
          </div>
          <div class="hands" :class="{ cover: isPasswordFocused }">
            <div class="hand hand-left"></div>
            <div class="hand hand-right"></div>
          </div>
        </div>
      </div>

      <h2 class="login-title">健康趋势分析</h2>
      <p class="login-subtitle">检查报告趋势追踪系统</p>

      <el-tabs v-model="tab" class="login-tabs" :stretch="true">
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <el-form v-if="tab === 'login'" :model="form" @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="手机号 / 用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            placeholder="密码"
            type="password"
            size="large"
            :prefix-icon="Lock"
            show-password
            @focus="isPasswordFocused = true"
            @blur="isPasswordFocused = false"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" native-type="submit">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <el-form v-else :model="form" @submit.prevent="handleRegister" class="login-form">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="手机号 / 用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            placeholder="设置密码"
            type="password"
            size="large"
            :prefix-icon="Lock"
            show-password
            @focus="isPasswordFocused = true"
            @blur="isPasswordFocused = false"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" native-type="submit">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { login, register } from '../api/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const tab = ref('login')
const form = reactive({ username: '', password: '' })
const loading = ref(false)
const isPasswordFocused = ref(false)
const router = useRouter()
const authStore = useAuthStore()

const creatureRef = ref<HTMLElement | null>(null)
const eyeballLeft = ref<HTMLElement | null>(null)
const eyeballRight = ref<HTMLElement | null>(null)

function onMouseMove(e: MouseEvent) {
  if (!creatureRef.value) return
  const rect = creatureRef.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2 - 40
  const angle = Math.atan2(e.clientY - cy, e.clientX - cx)
  const maxMove = 6
  const dx = Math.cos(angle) * maxMove
  const dy = Math.sin(angle) * maxMove

  if (eyeballLeft.value) {
    eyeballLeft.value.style.transform = `translate(${dx}px, ${dy}px)`
  }
  if (eyeballRight.value) {
    eyeballRight.value.style.transform = `translate(${dx}px, ${dy}px)`
  }
}

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await login(form)
    authStore.setToken(res.data.access_token)
    await authStore.loadUser()
    await authStore.loadPatients()
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch {
    ElMessage.error('登录失败，请检查用户名密码')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await register(form)
    ElMessage.success('注册成功，请登录')
    tab.value = 'login'
  } catch {
    ElMessage.error('注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
  background: white;
  animation: float 20s infinite ease-in-out;
}

.bg-circle.c1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -200px;
  animation-delay: 0s;
}

.bg-circle.c2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: -100px;
  animation-delay: -7s;
}

.bg-circle.c3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 10%;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(20px, -30px) scale(1.05); }
  50% { transform: translate(-10px, 20px) scale(0.95); }
  75% { transform: translate(30px, 10px) scale(1.02); }
}

.login-card-wrapper {
  position: relative;
  z-index: 1;
  width: 400px;
  max-width: 100%;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  padding: 40px 32px 32px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(20px);
}

.creature {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.body {
  position: relative;
  width: 100px;
  height: 120px;
}

.ear {
  position: absolute;
  top: -8px;
  width: 28px;
  height: 28px;
  background: #ffb3d9;
  border-radius: 50% 50% 0 50%;
}

.ear-left { left: 10px; transform: rotate(-10deg); }
.ear-right { right: 10px; transform: rotate(90deg) scaleX(-1); }

.face {
  position: absolute;
  top: 14px;
  left: 10px;
  width: 80px;
  height: 80px;
  background: #ffb3d9;
  border-radius: 50%;
}

.eye {
  position: absolute;
  top: 24px;
  width: 26px;
  height: 26px;
  background: white;
  border-radius: 50%;
  overflow: hidden;
  transition: all 0.2s;
}

.eye-left { left: 12px; }
.eye-right { right: 12px; }

.eye.closed {
  height: 4px;
  border-radius: 2px;
  top: 36px;
}

.eye.closed .eyeball {
  display: none;
}

.eyeball {
  position: absolute;
  width: 14px;
  height: 14px;
  background: #2d3436;
  border-radius: 50%;
  top: 50%;
  left: 50%;
  margin-left: -7px;
  margin-top: -7px;
  transition: transform 0.08s ease-out;
}

.eyeball::after {
  content: '';
  position: absolute;
  width: 4px;
  height: 4px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
}

.nose {
  position: absolute;
  top: 44px;
  left: 50%;
  margin-left: -5px;
  width: 10px;
  height: 8px;
  background: #e88bab;
  border-radius: 0 0 50% 50%;
}

.mouth {
  position: absolute;
  top: 56px;
  left: 50%;
  margin-left: -8px;
  width: 16px;
  height: 6px;
  border-bottom: 3px solid #e88bab;
  border-radius: 0 0 50% 50%;
  transition: all 0.3s;
}

.mouth.smile {
  width: 20px;
  margin-left: -10px;
  height: 10px;
}

.hands {
  position: absolute;
  top: 54px;
  left: 0;
  width: 100px;
  height: 30px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
}

.hands.cover {
  opacity: 1;
}

.hand {
  position: absolute;
  width: 24px;
  height: 24px;
  background: #ffb3d9;
  border-radius: 50%;
  top: 0;
}

.hand-left { left: 8px; }
.hand-right { right: 8px; }

.login-title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.login-subtitle {
  text-align: center;
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 20px;
}

.login-tabs {
  margin-bottom: 20px;
}

.login-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.login-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
}

.login-form :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  border-radius: 12px;
  padding: 8px 12px;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #818cf8 inset;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

@media (max-width: 480px) {
  .login-card-wrapper {
    padding: 32px 20px 24px;
  }
}
</style>
