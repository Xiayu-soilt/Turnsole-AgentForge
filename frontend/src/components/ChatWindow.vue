<template>
  <div class="chat-window">
    <div class="chat-messages" ref="messagesRef">
      <div v-if="messages.length === 0" class="chat-empty">
        <svg class="empty-logo" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="petalGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#ffc53d" />
              <stop offset="100%" stop-color="#f59f00" />
            </linearGradient>
          </defs>
          <g transform="translate(50 50)">
            <g fill="url(#petalGrad2)" stroke="#e8930c" stroke-width="1">
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
        <div class="empty-title">{{ botInfo.welcome_message || '你好！' }}</div>
        <div class="empty-sub">基于企业知识库回答，内容有据可查</div>
        <div class="suggest-box" v-if="botInfo.suggested_questions && botInfo.suggested_questions.length">
          <div
            v-for="(q, i) in botInfo.suggested_questions"
            :key="i"
            class="suggest-item"
            @click="sendMessage(q)"
          >
            <el-icon><ChatLineRound /></el-icon>
            <span>{{ q }}</span>
          </div>
        </div>
      </div>

      <div v-for="msg in messages" :key="msg.id" class="msg-row" :class="msg.role">
        <div class="avatar" :class="msg.role">
          <span v-if="msg.role === 'user'">{{ userInitial }}</span>
          <svg v-else class="bot-avatar" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <g transform="rotate(15 50 50)">
              <path
                d="M50 3 L42 22 L30 14 L33 30 L14 25 L26 38 L6 40 L24 50 L6 60 L26 62 L14 75 L33 70 L30 86 L42 78 L50 97 L58 78 L70 86 L67 70 L86 75 L74 62 L94 60 L76 50 L94 40 L74 38 L86 25 L67 30 L70 14 L58 22 Z"
                fill="#fff"
              />
            </g>
          </svg>
        </div>
        <div class="bubble-wrap">
          <div class="bubble" :class="msg.role">
            <div class="bubble-content markdown-body" v-html="renderMarkdown(msg.content || (msg.streaming ? ' ' : ''))"></div>
            <span v-if="msg.streaming" class="cursor">▍</span>
          </div>

          <div v-if="msg.role === 'assistant' && !msg.streaming && msg.citations && msg.citations.length" class="citations">
            <div class="citation-title">
              <el-icon><Link /></el-icon> 引用来源 ({{ msg.citations.length }})
            </div>
            <el-collapse class="citation-collapse">
              <el-collapse-item
                v-for="c in msg.citations"
                :key="c.index"
                :title="`[${c.index}] ${c.filename || '知识片段'} · 相关度 ${(c.score * 100).toFixed(0)}%`"
                :name="c.index"
              >
                <div class="citation-content">{{ c.content }}</div>
              </el-collapse-item>
            </el-collapse>
          </div>

          <div
            v-if="msg.role === 'assistant' && !msg.streaming && !publicMode"
            class="feedback-bar"
          >
            <el-tooltip content="有帮助" placement="top">
              <el-icon
                class="fb-icon"
                :class="{ active: msg.feedback === 'like' }"
                @click="sendFeedback(msg, 'like')"
              >
                <CaretTop />
              </el-icon>
            </el-tooltip>
            <el-tooltip content="无帮助" placement="top">
              <el-icon
                class="fb-icon"
                :class="{ active: msg.feedback === 'dislike' }"
                @click="sendFeedback(msg, 'dislike')"
              >
                <CaretBottom />
              </el-icon>
            </el-tooltip>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-box">
      <el-input
        v-model="inputText"
        :disabled="streaming"
        placeholder="输入你的问题，Enter 发送..."
        size="large"
        @keyup.enter="handleEnter"
      >
        <template #append>
          <el-button :loading="streaming" @click="handleEnter" class="send-btn">
            {{ streaming ? '生成中' : '发送' }}
          </el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import api from '../api'
import { streamChat } from '../api/stream'
import { ElMessage } from 'element-plus'

const props = defineProps({
  botId: { type: Number, default: null },
  publishToken: { type: String, default: '' },
  botInfo: {
    type: Object,
    default: () => ({
      name: '智能体',
      welcome_message: '你好，请问有什么可以帮您？',
      suggested_questions: [],
    }),
  },
  publicMode: { type: Boolean, default: false },
})

const messagesRef = ref(null)
const inputText = ref('')
const streaming = ref(false)
const messages = ref([])
let msgCounter = 1
const sessionKey = `s_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

const userInitial = computed(() => (localStorage.getItem('username') || 'I').charAt(0).toUpperCase())

marked.setOptions({
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
})

function renderMarkdown(text) {
  try {
    return marked.parse(text || '')
  } catch {
    return text
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function handleEnter() {
  const text = inputText.value.trim()
  if (!text || streaming.value) return
  inputText.value = ''
  sendMessage(text)
}

function sendMessage(text) {
  if (streaming.value) return
  streaming.value = true

  const userMsg = { id: `u${msgCounter++}`, role: 'user', content: text }
  const aiMsg = {
    id: `a${msgCounter++}`,
    role: 'assistant',
    content: '',
    streaming: true,
    citations: [],
    feedback: null,
  }
  messages.value.push(userMsg, aiMsg)
  scrollToBottom()

  const endpoint = props.publicMode
    ? `/api/public/${props.publishToken}/stream`
    : `/api/chat/${props.botId}/stream`

  streamChat({
    endpoint,
    payload: { message: text, session_key: sessionKey },
    onChunk: (data) => {
      aiMsg.content += data.content
      scrollToBottom()
    },
    onDone: (data) => {
      aiMsg.streaming = false
      aiMsg.citations = data.citations || []
      aiMsg.id = data.assistant_message_id || aiMsg.id
      streaming.value = false
      scrollToBottom()
    },
    onError: (data) => {
      aiMsg.streaming = false
      if (!aiMsg.content) {
        aiMsg.content = `抱歉，生成回答时出现问题：${data.message || '未知错误'}`
      }
      streaming.value = false
      ElMessage.error(data.message || '生成失败')
    },
  })
}

async function sendFeedback(msg, action) {
  try {
    const final = msg.feedback === action ? 'none' : action
    await api.post(`/api/chat/messages/${msg.id}/feedback?action=${final}`)
    msg.feedback = final === 'none' ? null : final
  } catch {
    ElMessage.error('反馈失败')
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fafbfc;
  border-radius: 12px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 60px;
  text-align: center;
}

.empty-logo {
  width: 72px;
  height: 72px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 19px;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-sub {
  color: #9aa3af;
  font-size: 14px;
  margin-bottom: 28px;
}

.suggest-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 70%;
  max-width: 420px;
}

.suggest-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1px solid #eceef2;
  border-radius: 10px;
  padding: 12px 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.suggest-item:hover {
  border-color: #f5a623;
  color: #d48806;
  transform: translateY(-1px);
}

.msg-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.msg-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 700;
  color: #fff;
  font-size: 15px;
}

.avatar.user {
  background: linear-gradient(135deg, #5b8def, #3b6ee0);
}

.avatar.assistant {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
}

.bot-avatar {
  width: 20px;
  height: 20px;
}

.bubble-wrap {
  max-width: 78%;
  min-width: 0;
}

.bubble {
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 15px;
  line-height: 1.7;
  word-break: break-word;
}

.bubble.user {
  background: linear-gradient(135deg, #5b8def, #3b6ee0);
  color: #fff;
  border-top-right-radius: 4px;
}

.bubble.assistant {
  background: #fff;
  border: 1px solid #eceef2;
  border-top-left-radius: 4px;
}

.cursor {
  animation: blink 0.8s infinite;
  color: #f5a623;
  font-weight: bold;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.citations {
  margin-top: 10px;
}

.citation-title {
  font-size: 13px;
  color: #8a919e;
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
}

.citation-collapse {
  border: none;
}

.citation-collapse :deep(.el-collapse-item__header) {
  font-size: 13px;
  color: #6b7280;
  background: #fff;
  border-radius: 8px;
  padding: 0 12px;
  border: 1px solid #f0f1f5;
  margin-bottom: 6px;
  height: 40px;
}

.citation-collapse :deep(.el-collapse-item__wrap) {
  border: none;
}

.citation-content {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  background: #fffaf0;
  border-radius: 8px;
  padding: 10px 12px;
  max-height: 160px;
  overflow-y: auto;
}

.feedback-bar {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.fb-icon {
  font-size: 16px;
  color: #c4c9d4;
  cursor: pointer;
  transition: all 0.2s;
}

.fb-icon:hover {
  color: #8a919e;
}

.fb-icon.active {
  color: #f5a623;
}

.chat-input-box {
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #eceef2;
  border-radius: 0 0 12px 12px;
}

.send-btn {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  border: none;
  color: #fff;
  padding: 0 20px;
}

.send-btn:hover {
  color: #fff;
  opacity: 0.9;
}
</style>
