<template>
  <div class="public-page">
    <div class="public-card">
      <div class="public-head">
        <div class="public-bot-avatar">
          <svg class="pub-sunflower" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(50 50)">
              <g fill="#fff">
                <ellipse rx="8" ry="18" cy="-23" />
                <ellipse rx="8" ry="18" cy="-23" transform="rotate(45)" />
                <ellipse rx="8" ry="18" cy="-23" transform="rotate(90)" />
                <ellipse rx="8" ry="18" cy="-23" transform="rotate(135)" />
                <ellipse rx="8" ry="18" cy="-23" transform="rotate(180)" />
                <ellipse rx="8" ry="18" cy="-23" transform="rotate(225)" />
                <ellipse rx="8" ry="18" cy="-23" transform="rotate(270)" />
                <ellipse rx="8" ry="18" cy="-23" transform="rotate(315)" />
              </g>
              <circle r="12" fill="#a06c35" />
              <circle r="8" fill="#8a5a2b" />
            </g>
          </svg>
        </div>
        <div>
          <div class="public-bot-name">{{ botInfo.name }}</div>
          <div class="public-bot-sub">Powered by Turnsole AgentForge · 企业知识库智能问答</div>
        </div>
      </div>

      <div class="public-chat-area">
        <ChatWindow
          v-if="loaded"
          :publish-token="token"
          :bot-info="botInfo"
          :public-mode="true"
        />
        <div v-else class="public-loading">
          <el-icon class="is-loading" :size="28" color="#f5a623"><Loading /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import ChatWindow from '../components/ChatWindow.vue'

const route = useRoute()
const token = route.params.token
const botInfo = ref({
  name: '智能助手',
  welcome_message: '你好，请问有什么可以帮您？',
  suggested_questions: [],
})
const loaded = ref(false)

onMounted(async () => {
  try {
    const res = await api.get(`/api/public/${token}/info`)
    botInfo.value = res.data
    loaded.value = true
  } catch {
    botInfo.value = {
      name: '智能体不可用',
      welcome_message: '该智能体不存在或已下线',
      suggested_questions: [],
    }
    loaded.value = true
  }
})
</script>

<style scoped>
.public-page {
  height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #fdf9ec, #fdf0d5 60%, #fce7bd);
  padding: 24px;
}

.public-card {
  width: 480px;
  max-width: 100%;
  height: min(760px, 92vh);
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 24px 60px rgba(200, 150, 50, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.public-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 22px;
  border-bottom: 1px solid #f5ece8;
  background: linear-gradient(135deg, #ffc53d, #f5a623);
}

.public-bot-avatar {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pub-sunflower {
  width: 26px;
  height: 26px;
}

.public-bot-name {
  color: #fff;
  font-size: 19px;
  font-weight: 700;
}

.public-bot-sub {
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  margin-top: 2px;
}

.public-chat-area {
  flex: 1;
  min-height: 0;
}

.public-loading {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
