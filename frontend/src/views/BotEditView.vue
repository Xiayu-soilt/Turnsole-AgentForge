<template>
  <div v-if="bot" class="edit-layout">
    <div class="config-panel card">
      <div class="edit-header">
        <el-button text @click="router.push('/bots')">
          <el-icon><ArrowLeft /></el-icon>&nbsp;返回
        </el-button>
        <span class="edit-title">智能体配置</span>
      </div>

      <el-form label-position="top" size="large" class="config-form">
        <el-form-item label="名称">
          <el-input v-model="bot.name" maxlength="100" />
        </el-form-item>

        <el-form-item>
          <template #label>
            <div class="ai-label-row">
              <span>AI 一键生成配置</span>
              <div class="ai-label-controls">
                <el-select v-model="aiStyle" size="small" class="style-select">
                  <el-option value="professional" label="专业严谨" />
                  <el-option value="friendly" label="亲切友善" />
                  <el-option value="humorous" label="幽默风趣" />
                  <el-option value="concise" label="简洁干练" />
                </el-select>
                <el-button
                  class="ai-gen-btn"
                  size="small"
                  :loading="aiLoading"
                  @click="aiPersona"
                >
                  <el-icon v-if="!aiLoading"><MagicStick /></el-icon>&nbsp;AI 智能生成
                </el-button>
              </div>
            </div>
          </template>
          <div class="ai-hint">
            根据当前名称与绑定的知识库，AI 一次性重写人设、开场白与推荐问题
          </div>
        </el-form-item>

        <el-form-item label="人设提示词（System Prompt）">
          <el-input
            v-model="bot.system_prompt"
            type="textarea"
            :rows="5"
            placeholder="定义智能体的角色、语气与专业领域。例如：你是「XX科技」的客服主管，语气亲切专业，擅长解答产品使用问题..."
          />
          <div class="field-tip">智能体会严格基于知识库回答，人设决定它的语气与角色</div>
        </el-form-item>

        <el-form-item label="开场白">
          <el-input v-model="bot.welcome_message" type="textarea" :rows="2" />
        </el-form-item>

        <el-form-item label="推荐问题（每行一个）">
          <el-input
            v-model="suggestedText"
            type="textarea"
            :rows="3"
            placeholder="如何申请退款？&#10;上班时间是几点？"
          />
        </el-form-item>

        <el-form-item label="绑定知识库（多选）">
          <el-select v-model="bot.kb_ids" multiple style="width: 100%" placeholder="选择知识库">
            <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <template #label>
            <span>创造性（temperature:&nbsp;{{ bot.temperature }}&nbsp;）</span>
          </template>
          <el-slider v-model="bot.temperature" :min="0" :max="1.5" :step="0.1" />
          <div class="field-tip">越低越严谨（客服场景建议 0.3 以下），越高越有创造性</div>
        </el-form-item>

        <el-button type="primary" size="large" class="save-btn" :loading="saving" @click="saveBot">
          保存配置
        </el-button>

        <el-divider>发布</el-divider>

        <div class="publish-box">
          <template v-if="!bot.is_published">
            <el-button type="success" size="large" class="pub-btn" @click="publish">
              <el-icon><Promotion /></el-icon>&nbsp;发布智能体
            </el-button>
            <div class="field-tip">发布后获得公开链接，可分享给任何人使用</div>
          </template>
          <template v-else>
            <el-alert type="success" :closable="false" show-icon>
              <div class="pub-link">{{ publicUrl }}</div>
            </el-alert>
            <div class="pub-actions">
              <el-button @click="copyLink"><el-icon><Link /></el-icon>&nbsp;复制链接</el-button>
              <el-button @click="copyIframe"><el-icon><Code /></el-icon>&nbsp;复制嵌入代码</el-button>
              <el-button type="warning" plain @click="unpublish">下线</el-button>
            </div>
            <div class="field-tip">嵌入代码可放置到任意网站，智能体即在网站内可用</div>
          </template>
        </div>
      </el-form>
    </div>

    <div class="debug-panel card">
      <div class="debug-head">
        <span class="debug-title">
          <el-icon color="#d48806"><ChatDotRound /></el-icon>
          实时调试
        </span>
        <el-tag size="small" effect="plain" round type="info">未保存的配置不会生效</el-tag>
      </div>
      <div class="debug-chat">
        <ChatWindow :bot-id="bot.id" :bot-info="chatBotInfo" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import api from '../api'
import ChatWindow from '../components/ChatWindow.vue'

const route = useRoute()
const router = useRouter()
const bot = ref(null)
const kbs = ref([])
const saving = ref(false)
const suggestedText = ref('')
const aiLoading = ref(false)
const aiStyle = ref('friendly')

async function aiPersona() {
  if (!bot.value?.name?.trim()) {
    ElMessage.warning('请先填写智能体名称')
    return
  }
  aiLoading.value = true
  try {
    const kbNames = kbs.value
      .filter((kb) => (bot.value.kb_ids || []).includes(kb.id))
      .map((kb) => kb.name)
    const res = await api.post(
      '/api/ai/agent-profile',
      {
        name: bot.value.name.trim(),
        kb_names: kbNames,
        style: aiStyle.value,
      },
      { timeout: 120000 }
    )
    const d = res.data
    if (d.system_prompt) bot.value.system_prompt = d.system_prompt
    if (d.welcome_message) bot.value.welcome_message = d.welcome_message
    if (d.suggested_questions?.length) {
      suggestedText.value = d.suggested_questions.join('\n')
    }
    ElMessage.success('AI 已生成完整配置，记得保存')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || 'AI 生成失败，请稍后重试')
  } finally {
    aiLoading.value = false
  }
}

const chatBotInfo = computed(() => ({
  name: bot.value?.name || '智能体',
  welcome_message: bot.value?.welcome_message || '你好，保存配置后即可开始调试',
  suggested_questions: suggestedText.value
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean),
}))

const publicUrl = computed(
  () => `${window.location.origin}/chat/${bot.value?.publish_token || ''}`
)

async function loadBot() {
  const res = await api.get(`/api/bots/${route.params.id}`)
  bot.value = res.data
  suggestedText.value = (res.data.suggested_questions || []).join('\n')
}

async function loadKbs() {
  const res = await api.get('/api/kb')
  kbs.value = res.data
}

async function saveBot() {
  if (!bot.value.name.trim()) {
    ElMessage.warning('名称不能为空')
    return
  }
  saving.value = true
  try {
    await api.put(`/api/bots/${bot.value.id}`, {
      name: bot.value.name,
      system_prompt: bot.value.system_prompt,
      welcome_message: bot.value.welcome_message,
      suggested_questions: suggestedText.value
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean),
      kb_ids: bot.value.kb_ids,
      temperature: bot.value.temperature,
    })
    ElMessage.success('配置已保存')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function publish() {
  try {
    const res = await api.post(`/api/bots/${bot.value.id}/publish`)
    bot.value.is_published = true
    bot.value.publish_token = res.data.publish_token
    ElMessage.success('发布成功')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '发布失败')
  }
}

async function unpublish() {
  await api.post(`/api/bots/${bot.value.id}/unpublish`)
  bot.value.is_published = false
  ElMessage.success('已下线')
}

async function copyLink() {
  await navigator.clipboard.writeText(publicUrl.value)
  ElMessage.success('链接已复制')
}

async function copyIframe() {
  const code = `<iframe src="${publicUrl.value}" width="420" height="640" style="border:none;border-radius:12px" allow="microphone"></iframe>`
  await navigator.clipboard.writeText(code)
  ElMessage.success('嵌入代码已复制')
}

onMounted(() => {
  loadBot()
  loadKbs()
})
</script>

<style scoped>
.edit-layout {
  display: grid;
  grid-template-columns: 1fr 480px;
  gap: 16px;
  height: calc(100vh - 110px);
  align-items: stretch;
}

.config-panel {
  overflow-y: auto;
  padding: 20px 28px;
}

.edit-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.edit-title {
  font-size: 19px;
  font-weight: 700;
}

.config-form {
  max-width: 640px;
}

.field-tip {
  font-size: 12px;
  color: #9aa3af;
  margin-top: 6px;
  line-height: 1.5;
}

.save-btn {
  width: 200px;
  height: 46px;
  font-size: 16px;
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  border: none;
}

.publish-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pub-btn {
  width: 220px;
  height: 46px;
  font-size: 16px;
}

.pub-link {
  font-size: 13px;
  word-break: break-all;
}

.pub-actions {
  display: flex;
  gap: 10px;
}

.debug-panel {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.debug-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f1f5;
}

.debug-title {
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6px;
}

.debug-chat {
  flex: 1;
  min-height: 0;
}

/* ---------- AI 生成 ---------- */

.ai-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 4px;
}

.ai-label-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.style-select {
  width: 108px;
}

.ai-hint {
  font-size: 12px;
  color: #b0a895;
  background: #fdf8ec;
  border-radius: 8px;
  padding: 8px 12px;
  width: 100%;
}

.ai-gen-btn {
  border: none;
  border-radius: 8px;
  color: #fff;
  font-weight: 600;
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  box-shadow: 0 2px 8px rgba(245, 166, 35, 0.26);
}

.ai-gen-btn:hover {
  color: #fff;
  background: linear-gradient(135deg, #ffd25e, #f7ae2e);
}
</style>
