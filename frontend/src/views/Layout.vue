<template>
  <el-container class="layout">
    <el-aside width="230px" class="aside">
      <div class="logo-box">
        <svg class="logo-mark" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="petalGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#ffc53d" />
              <stop offset="100%" stop-color="#f59f00" />
            </linearGradient>
          </defs>
          <g transform="translate(50 50)">
            <g fill="url(#petalGrad)" stroke="#e8930c" stroke-width="1">
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
        <div class="logo-text">
          <span class="logo-name">Turnsole AgentForge</span>
          <span class="logo-sub">AI 智能体工厂</span>
        </div>
      </div>

      <el-menu :default-active="activeMenu" router class="side-menu">
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/bots">
          <el-icon><Service /></el-icon>
          <span>我的智能体</span>
        </el-menu-item>
        <el-menu-item index="/square">
          <el-icon><Compass /></el-icon>
          <span>智能体广场</span>
        </el-menu-item>
        <el-menu-item index="/audit">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话审计</span>
        </el-menu-item>
      </el-menu>

      <div class="aside-footer">
        <div class="user-chip">
          <el-avatar :size="36" class="user-avatar">{{ username.charAt(0).toUpperCase() }}</el-avatar>
          <div class="user-info">
            <div class="user-name">{{ username }}</div>
            <div class="user-company">{{ company }}</div>
          </div>
        </div>
        <el-button text class="logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon> 退出登录
        </el-button>
      </div>
    </el-aside>

    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const username = computed(() => userStore.username || '用户')
const company = computed(() => userStore.company || '我的企业')
const activeMenu = computed(() => '/' + (route.path.split('/')[1] || 'dashboard'))

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '退出',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      userStore.logout()
      router.push('/login')
    })
    .catch(() => {})
}
</script>

<style scoped>
.layout {
  height: 100%;
}

.aside {
  background: #fff;
  border-right: 1px solid #eceef2;
  display: flex;
  flex-direction: column;
}

.logo-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 18px 16px;
}

.logo-mark {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-name {
  font-size: 21px;
  font-weight: 800;
  background: linear-gradient(135deg, #f7b733, #e8930c);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  line-height: 1.2;
}

.logo-sub {
  font-size: 12px;
  color: #9aa3af;
}

.side-menu {
  border-right: none;
  flex: 1;
  padding: 8px;
}

.side-menu .el-menu-item {
  height: 48px;
  font-size: 15px;
  border-radius: 10px;
  margin-bottom: 4px;
}

.side-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #fdf3dd, #fce7bd);
  color: #d48806;
  font-weight: 600;
}

.aside-footer {
  padding: 14px;
  border-top: 1px solid #f0f1f5;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.user-avatar {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  color: #fff;
  font-weight: 700;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
}

.user-company {
  font-size: 12px;
  color: #9aa3af;
}

.logout-btn {
  width: 100%;
  color: #8a919e;
}

.main {
  background: #f7f4ea;
  padding: 24px 28px;
  overflow-y: auto;
}
</style>
