<template>
  <div class="login-page">
    <div class="bg-carousel">
      <div
        v-for="(img, i) in backgrounds"
        :key="i"
        class="bg-slide"
        :class="{ active: i === current }"
        :style="{ backgroundImage: `url(${img})` }"
      ></div>
      <div class="bg-mask"></div>
    </div>

    <div class="dots">
      <span
        v-for="(img, i) in backgrounds"
        :key="i"
        class="dot"
        :class="{ active: i === current }"
        @click="switchTo(i)"
      ></span>
    </div>

    <div class="login-card">
      <div class="card-header">
        <svg class="card-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="petalGrad3" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#ffc53d" />
              <stop offset="100%" stop-color="#f59f00" />
            </linearGradient>
          </defs>
          <g transform="translate(50 50)">
            <g fill="url(#petalGrad3)" stroke="#e8930c" stroke-width="1">
              <ellipse rx="9" ry="21" cy="-26" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(45)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(90)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(135)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(180)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(225)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(270)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(315)" />
            </g>
            <circle r="14" fill="#8a5a2b" />
            <circle r="10" fill="#a06c35" />
            <g fill="#6f451f">
              <circle r="1.3" cx="-4" cy="-3" />
              <circle r="1.3" cx="4" cy="-3" />
              <circle r="1.3" cx="-4" cy="3" />
              <circle r="1.3" cx="4" cy="3" />
              <circle r="1.3" cx="0" cy="0" />
            </g>
          </g>
        </svg>
        <div class="card-title">
          <h1>Turnsole AgentForge</h1>
          <p>AI 企业智能体工厂</p>
        </div>
      </div>

      <div class="card-desc">上传企业知识 · 配置专属人设 · 一键发布智能助手</div>

      <el-tabs v-model="activeTab" stretch class="login-tabs">
        <el-tab-pane label="登 录" name="login">
          <el-form size="large" @submit.prevent>
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                show-password
                :prefix-icon="Lock"
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-button class="submit-btn" size="large" :loading="loading" @click="handleLogin">
              登 录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注 册" name="register">
          <el-form size="large" @submit.prevent>
            <el-form-item>
              <el-input v-model="regForm.company" placeholder="企业 / 团队名称" :prefix-icon="OfficeBuilding" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.username" placeholder="用户名（2-64 字符）" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="regForm.password"
                type="password"
                placeholder="密码（至少 6 位）"
                show-password
                :prefix-icon="Lock"
                @keyup.enter="handleRegister"
              />
            </el-form-item>
            <el-button class="submit-btn" size="large" :loading="loading" @click="handleRegister">
              创建企业空间
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, OfficeBuilding } from '@element-plus/icons-vue'
import api from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const activeTab = ref('login')

const backgrounds = [
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=%E7%8E%B0%E4%BB%A3%E4%BC%81%E4%B8%9A%E5%8A%9E%E5%85%AC%E5%AE%A4%E9%87%8C%E6%99%BA%E8%83%BD%E6%9C%BA%E5%99%A8%E4%BA%BA%E5%8A%A9%E6%89%8B%E5%8D%8F%E4%BD%9C%E5%9C%BA%E6%99%AF%EF%BC%8C%E6%89%81%E5%B9%B3%E9%A3%8E%E6%A0%BC%E6%8F%92%E7%94%BB%EF%BC%8C%E7%BA%A2%E6%A9%99%E6%B8%90%E5%8F%98%E6%9A%96%E8%89%B2%E8%B0%83%EF%BC%8C%E5%B9%B2%E5%87%80%E7%AE%80%E7%BA%A6%E8%83%8C%E6%99%AF%EF%BC%8C%E5%A4%A7%E9%9D%A2%E7%A7%AF%E7%95%99%E7%99%BD&image_size=landscape_16_9',
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=%E6%95%B0%E5%AD%97%E7%9F%A5%E8%AF%86%E7%BD%91%E7%BB%9C%E8%8A%82%E7%82%B9%E4%B8%8E%E8%BF%9E%E7%BA%BF%E6%8A%BD%E8%B1%A1%E6%8F%92%E7%94%BB%EF%BC%8C%E7%A7%91%E6%8A%80%E6%84%9F%EF%BC%8C%E6%A9%99%E7%BA%A2%E8%89%B2%E6%B8%90%E5%8F%98%E4%B8%BB%E8%89%B2%EF%BC%8C%E5%B9%B2%E5%87%80%E8%83%8C%E6%99%AF%E5%B0%91%E9%87%8F%E5%85%83%E7%B4%A0&image_size=landscape_16_9',
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=%E6%9C%AA%E6%9D%A5%E5%B7%A5%E5%8E%82%E4%BC%A0%E9%80%81%E5%B8%A6%E4%B8%8A%E7%9A%84%E5%B0%8F%E6%9C%BA%E5%99%A8%E4%BA%BA%E7%8E%A9%E5%81%B6%E6%8F%92%E7%94%BB%EF%BC%8C%E7%BA%A2%E6%A9%99%E6%9A%96%E8%89%B2%E8%B0%83%EF%BC%8C%E6%89%81%E5%B9%B3%E9%A3%8E%E6%A0%BC%EF%BC%8C%E7%AE%80%E6%B4%81%E6%9E%84%E5%9B%BE%EF%BC%8C%E7%99%BD%E8%89%B2%E4%BA%AE%E9%83%A8&image_size=landscape_16_9',
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=%E5%88%9B%E6%84%8F%E7%81%AF%E6%B3%A1%E4%B8%8E%E9%BD%BF%E8%BD%AE%E7%BB%84%E5%90%88%E6%8F%92%E7%94%BB%EF%BC%8C%E8%B1%A1%E5%BE%81%E6%99%BA%E8%83%BD%E5%88%9B%E6%96%B0%EF%BC%8C%E6%A9%99%E7%BA%A2%E6%B8%90%E5%8F%98%E8%89%B2%E7%B3%BB%EF%BC%8C%E6%9E%81%E7%AE%80%E6%9E%84%E5%9B%BE%EF%BC%8C%E5%B9%B2%E5%87%80%E7%99%BD%E8%83%8C%E6%99%AF&image_size=landscape_16_9',
]

const current = ref(Math.floor(Math.random() * backgrounds.length))
let timer = null

function switchTo(index) {
  current.value = index
  resetTimer()
}

function resetTimer() {
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    current.value = (current.value + 1) % backgrounds.length
  }, 10000)
}

onMounted(() => {
  resetTimer()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const loginForm = ref({ username: '', password: '' })
const regForm = ref({ company: '', username: '', password: '' })

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await api.post('/api/auth/login', loginForm.value)
    userStore.setLogin(res.data)
    ElMessage.success(`欢迎回来，${res.data.username}`)
    router.push('/dashboard')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const { company, username, password } = regForm.value
  if (!company || !username || !password) {
    ElMessage.warning('请完整填写注册信息')
    return
  }
  if (password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  loading.value = true
  try {
    const res = await api.post('/api/auth/register', regForm.value)
    userStore.setLogin(res.data)
    ElMessage.success('注册成功，已自动登录')
    router.push('/knowledge')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bg-carousel {
  position: absolute;
  inset: 0;
}

.bg-slide {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  opacity: 0;
  transition: opacity 1.5s ease-in-out;
}

.bg-slide.active {
  opacity: 1;
}

.bg-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 250, 247, 0.72), rgba(255, 244, 240, 0.82));
  backdrop-filter: blur(2px);
}

.dots {
  position: absolute;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  z-index: 10;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(245, 166, 35, 0.3);
  cursor: pointer;
  transition: all 0.3s;
}

.dot:hover {
  background: rgba(245, 166, 35, 0.6);
}

.dot.active {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  transform: scale(1.25);
  box-shadow: 0 2px 8px rgba(245, 166, 35, 0.4);
}

.login-card {
  position: relative;
  z-index: 5;
  width: 420px;
  max-width: calc(100vw - 40px);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 36px 40px 30px;
  box-shadow: 0 20px 60px rgba(180, 140, 40, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}

.card-logo {
  width: 56px;
  height: 56px;
}

.card-title h1 {
  font-size: 30px;
  font-weight: 800;
  background: linear-gradient(135deg, #f7b733, #e8930c);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  line-height: 1.15;
}

.card-title p {
  color: #8a919e;
  font-size: 14px;
}

.card-desc {
  text-align: center;
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0e8e4;
}

.login-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 600;
}

.login-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  height: 3px;
  border-radius: 3px;
}

.submit-btn {
  width: 100%;
  height: 46px;
  font-size: 17px;
  font-weight: 600;
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  border: none;
  color: #fff;
  border-radius: 10px;
  letter-spacing: 4px;
}

.submit-btn:hover {
  opacity: 0.9;
  color: #fff;
}
</style>
