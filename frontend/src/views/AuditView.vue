<template>
  <div>
    <div class="page-header">
      <div class="page-title">对话审计</div>
      <div class="page-desc">追溯每一条对话的引用来源，评估回答质量</div>
    </div>

    <div class="audit-layout">
      <div class="card conv-panel">
        <div class="conv-head">会话列表（{{ conversations.length }}）</div>
        <div v-if="conversations.length === 0" class="conv-empty">暂无会话记录</div>
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: conv.id === activeConvId }"
          @click="loadDetail(conv.id)"
        >
          <div class="conv-item-head">
            <el-tag size="small" effect="plain" round>{{ sourceLabel(conv.source) }}</el-tag>
            <span class="conv-bot">{{ conv.bot_name }}</span>
          </div>
          <div class="conv-last">{{ conv.last_message }}</div>
          <div class="conv-meta">
            <span>{{ conv.message_count }} 条消息</span>
            <span>{{ formatTime(conv.created_at) }}</span>
          </div>
        </div>
      </div>

      <div class="card detail-panel">
        <template v-if="detail">
          <div class="detail-head">
            <div>
              <div class="detail-title">{{ detail.bot_name }} · 会话 #{{ detail.id }}</div>
              <div class="detail-sub">来源：{{ sourceLabel(detail.source) }} · {{ formatTime(detail.created_at) }}</div>
            </div>
          </div>
          <div class="detail-messages">
            <div v-for="msg in detail.messages" :key="msg.id" class="a-msg" :class="msg.role">
              <div class="a-role">{{ msg.role === 'user' ? '用户' : '智能体' }}</div>
              <div class="a-content">{{ msg.content }}</div>
              <div v-if="msg.citations && msg.citations.length" class="a-citations">
                <el-collapse>
                  <el-collapse-item
                    :title="`引用 ${msg.citations.length} 条知识片段`"
                    :name="msg.id"
                  >
                    <div
                      v-for="(c, i) in msg.citations"
                      :key="i"
                      class="a-citation-item"
                    >
                      <div class="a-citation-head">
                        <b>[{{ c.index }}]</b> {{ c.filename }} · 相关度
                        {{ (c.score * 100).toFixed(0) }}%
                      </div>
                      <div class="a-citation-body">{{ c.content }}</div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
              <div v-if="msg.feedback" class="a-feedback">
                <el-tag
                  size="small"
                  :type="msg.feedback === 'like' ? 'danger' : 'info'"
                  effect="plain"
                  round
                >
                  {{ msg.feedback === 'like' ? '用户点赞' : '用户点踩' }}
                </el-tag>
              </div>
            </div>
          </div>
        </template>
        <el-empty v-else description="选择左侧会话查看详情" :image-size="100" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../api'

const conversations = ref([])
const activeConvId = ref(null)
const detail = ref(null)

async function loadConversations() {
  const res = await api.get('/api/conversations')
  conversations.value = res.data
}

async function loadDetail(id) {
  activeConvId.value = id
  const res = await api.get(`/api/conversations/${id}`)
  detail.value = res.data
}

function sourceLabel(source) {
  return source === 'debug' ? '工作台调试' : '公开访问'
}

function formatTime(t) {
  return new Date(t).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadConversations)
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
}

.page-desc {
  color: #8a919e;
  margin-top: 4px;
}

.audit-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  height: calc(100vh - 150px);
}

.conv-panel {
  overflow-y: auto;
  padding: 16px;
}

.conv-head {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 12px;
}

.conv-empty {
  text-align: center;
  color: #c4c9d4;
  padding: 40px 0;
  font-size: 13px;
}

.conv-item {
  border: 1.5px solid transparent;
  border-radius: 10px;
  padding: 12px 14px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: all 0.2s;
  background: #fafbfc;
}

.conv-item:hover {
  border-color: #ffdfae;
}

.conv-item.active {
  border-color: #f5a623;
  background: #fffaf0;
}

.conv-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.conv-bot {
  font-size: 14px;
  font-weight: 600;
}

.conv-last {
  font-size: 13px;
  color: #6b7280;
  margin: 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #9aa3af;
}

.detail-panel {
  overflow-y: auto;
  padding: 20px 24px;
}

.detail-head {
  margin-bottom: 16px;
}

.detail-title {
  font-size: 18px;
  font-weight: 700;
}

.detail-sub {
  font-size: 13px;
  color: #9aa3af;
  margin-top: 4px;
}

.a-msg {
  margin-bottom: 18px;
}

.a-role {
  font-size: 12px;
  font-weight: 700;
  color: #9aa3af;
  margin-bottom: 6px;
}

.a-msg.user .a-role {
  color: #3b6ee0;
}

.a-msg.assistant .a-role {
  color: #d48806;
}

.a-content {
  background: #fafbfc;
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.a-msg.user .a-content {
  background: #eef4ff;
}

.a-citations {
  margin-top: 8px;
}

.a-citation-item {
  margin-bottom: 10px;
}

.a-citation-head {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.a-citation-body {
  font-size: 13px;
  color: #9aa3af;
  background: #fffaf0;
  border-radius: 8px;
  padding: 10px;
  line-height: 1.6;
}

.a-feedback {
  margin-top: 6px;
}
</style>
