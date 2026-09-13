<template>
  <div class="square-page">
    <div class="square-bg-blob blob-a"></div>
    <div class="square-bg-blob blob-b"></div>

    <header class="square-header">
      <div class="square-brand">
        <svg class="brand-sunflower" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <g transform="translate(50 50)">
            <g fill="#f5a623">
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
            <circle r="9" fill="#a06c35" />
          </g>
        </svg>
        <span class="brand-name">Turnsole AgentForge</span>
      </div>
      <el-button round size="large" class="console-btn" @click="goConsole">
        {{ isLoggedIn ? '进入控制台' : '登录 / 注册' }}
      </el-button>
    </header>

    <section class="square-hero">
      <h1 class="hero-title">智能体广场</h1>
      <p class="hero-sub">
        这里汇集了平台上所有已发布的 <span class="hero-highlight">知识库智能体</span>
        <br />
        无需注册，点击即可开聊；注册后还能免费创建属于你的智能体
      </p>
    </section>

    <section class="square-grid" v-loading="loading">
      <div v-for="agent in agents" :key="agent.publish_token" class="agent-card" @click="tryAgent(agent)">
        <div class="agent-avatar" :style="{ background: avatarColor(agent.name) }">
          {{ agent.name.charAt(0) }}
        </div>
        <div class="agent-info">
          <div class="agent-name">{{ agent.name }}</div>
          <div class="agent-company">{{ agent.company || 'Turnsole AgentForge 用户' }}</div>
          <div class="agent-welcome">"{{ agent.welcome_message }}"</div>
          <div class="agent-meta">
            <el-tag size="small" effect="plain" round>{{ agent.kb_count }} 个知识库</el-tag>
          </div>
        </div>
        <div class="agent-go">
          <el-icon><ChatDotRound /></el-icon>
        </div>
      </div>

      <div v-if="!loading && agents.length === 0" class="square-empty">
        <svg class="empty-flower" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <g transform="translate(50 50)">
            <g fill="#f8d9a0">
              <ellipse rx="9" ry="21" cy="-26" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(45)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(90)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(135)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(180)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(225)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(270)" />
              <ellipse rx="9" ry="21" cy="-26" transform="rotate(315)" />
            </g>
            <circle r="14" fill="#e0c9a0" />
          </g>
        </svg>
        <div class="empty-title">广场还没有智能体入驻</div>
        <div class="empty-sub">登录控制台，创建并发布你的第一个智能体</div>
        <el-button type="primary" round size="large" class="empty-btn" @click="goConsole">
          开始创建
        </el-button>
      </div>
    </section>

    <footer class="square-footer">Turnsole AgentForge · 让每个企业都拥有自己的智能体</footer>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const agents = ref([])
const loading = ref(false)
const isLoggedIn = ref(!!localStorage.getItem('token'))

const AVATAR_GRADIENTS = [
  'linear-gradient(135deg, #ffc53d, #f5a623)',
  'linear-gradient(135deg, #ff8a65, #ff7043)',
  'linear-gradient(135deg, #8bc34a, #558b2f)',
  'linear-gradient(135deg, #4fc3f7, #0288d1)',
  'linear-gradient(135deg, #b39ddb, #7e57c2)',
  'linear-gradient(135deg, #26a69a, #00897b)',
  'linear-gradient(135deg, #ef5350, #e53935)',
  'linear-gradient(135deg, #7986cb, #3f51b5)',
]

function avatarColor(name) {
  let hash = 0
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) % 997
  return AVATAR_GRADIENTS[hash % AVATAR_GRADIENTS.length]
}

function tryAgent(agent) {
  router.push(`/chat/${agent.publish_token}`)
}

function goConsole() {
  router.push(isLoggedIn.value ? '/dashboard' : '/login')
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/api/public/agents')
    agents.value = res.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.square-page {
  min-height: 100vh;
  background: linear-gradient(165deg, #fdf9ec 0%, #faf7ef 50%, #f4f2ea 100%);
  position: relative;
  overflow-x: hidden;
  padding-bottom: 60px;
}

.square-bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  pointer-events: none;
}

.blob-a {
  width: 420px;
  height: 420px;
  background: #ffe3a6;
  top: -120px;
  right: -100px;
}

.blob-b {
  width: 360px;
  height: 360px;
  background: #fce7bd;
  bottom: -100px;
  left: -120px;
}

.square-header {
  max-width: 1080px;
  margin: 0 auto;
  padding: 26px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
}

.square-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-sunflower {
  width: 36px;
  height: 36px;
}

.brand-name {
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, #f7b733, #e8930c);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.console-btn {
  font-weight: 600;
  border-color: #f5a623;
  color: #c4881d;
  background: #fffdf5;
}

.console-btn:hover {
  color: #c4881d;
  border-color: #f7b733;
  background: #fdf3dd;
}

.square-hero {
  text-align: center;
  padding: 40px 20px 36px;
  position: relative;
}

.hero-title {
  font-size: 42px;
  font-weight: 800;
  background: linear-gradient(135deg, #f7b733, #e8930c);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: 2px;
}

.hero-sub {
  margin-top: 14px;
  color: #8a8f9a;
  font-size: 16px;
  line-height: 1.9;
}

.hero-highlight {
  color: #d48806;
  font-weight: 700;
}

.square-grid {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
  position: relative;
  min-height: 200px;
}

.agent-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid #f2ecdc;
  border-radius: 18px;
  padding: 22px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}

.agent-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 14px 34px rgba(245, 166, 35, 0.2);
  border-color: #f5cd6f;
}

.agent-avatar {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  color: #fff;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  font-size: 17px;
  font-weight: 700;
}

.agent-company {
  font-size: 12px;
  color: #b0a895;
  margin-top: 2px;
}

.agent-welcome {
  font-size: 13px;
  color: #8a8f9a;
  margin: 10px 0;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-style: italic;
}

.agent-go {
  position: absolute;
  right: 18px;
  top: 20px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #fdf3dd;
  color: #d48806;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s ease;
}

.agent-card:hover .agent-go {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  color: #fff;
}

.square-empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 70px 0 50px;
}

.empty-flower {
  width: 84px;
  height: 84px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 700;
  color: #5a5346;
}

.empty-sub {
  color: #a39c8b;
  margin: 8px 0 22px;
  font-size: 14px;
}

.empty-btn {
  padding: 0 32px;
}

.square-footer {
  text-align: center;
  margin-top: 50px;
  color: #b0a895;
  font-size: 13px;
}
</style>
