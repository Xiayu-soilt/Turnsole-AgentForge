<template>
  <div>
    <div class="page-header">
      <div class="page-title">智能体</div>
      <div class="page-desc">配置人设与知识库，打造你的智能助手</div>
    </div>

    <div class="bot-grid">
      <div class="card new-bot-card" @click="showCreate = true">
        <el-icon :size="32" color="#f5a623"><CirclePlusFilled /></el-icon>
        <div class="new-bot-text">创建智能体</div>
      </div>

      <div v-for="bot in bots" :key="bot.id" class="card bot-card">
        <div class="bot-card-head">
          <div class="bot-avatar">
            <svg class="mini-sunflower" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
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
          <div class="bot-card-title">
            <div class="bot-name">{{ bot.name }}</div>
            <div class="bot-prompt">{{ bot.system_prompt || '默认人设' }}</div>
          </div>
        </div>

        <div class="bot-meta">
          <el-tag size="small" effect="plain" round type="info">
            {{ bot.kb_ids.length }} 个知识库
          </el-tag>
          <el-tag
            size="small"
            round
            :type="bot.is_published ? 'success' : 'warning'"
            effect="light"
          >
            {{ bot.is_published ? '已发布' : '未发布' }}
          </el-tag>
        </div>

        <div class="bot-actions">
          <el-button text type="primary" @click="router.push(`/bots/${bot.id}/edit`)">
            <el-icon><Edit /></el-icon>&nbsp;配置 / 调试
          </el-button>
          <el-dropdown trigger="click" @command="handleCommand($event, bot)">
            <el-button text type="info">
              <el-icon><More /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="publish" v-if="!bot.is_published">
                  <el-icon><Promotion /></el-icon>&nbsp;发布
                </el-dropdown-item>
                <el-dropdown-item command="unpublish" v-else>
                  <el-icon><VideoPause /></el-icon>&nbsp;下线
                </el-dropdown-item>
                <el-dropdown-item command="link" v-if="bot.is_published">
                  <el-icon><Link /></el-icon>&nbsp;复制公开链接
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided style="color: #f56c6c">
                  <el-icon><Delete /></el-icon>&nbsp;删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="创建智能体" width="520px">
      <el-form label-position="top" size="large">
        <el-form-item label="智能体名称" required>
          <el-input v-model="newBot.name" placeholder="如：小助手、IT 支持精灵、HR 问答官" maxlength="100" clearable />
        </el-form-item>
        <el-form-item>
          <template #label>
            <div class="ai-label-row">
              <span>AI 一键生成配置</span>
              <div class="ai-label-controls">
                <el-select v-model="newBot.style" size="small" class="style-select">
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
            输入名称并绑定知识库后点击生成，AI 将一次性产出人设、开场白与推荐问题
          </div>
        </el-form-item>
        <el-form-item label="人设提示词（System Prompt）">
          <el-input
            v-model="newBot.system_prompt"
            type="textarea"
            :rows="4"
            placeholder="例如：你是「XX科技」的 IT 支持助手，语气专业友善，回答简洁分点..."
            resize="none"
          />
        </el-form-item>
        <el-form-item label="开场白">
          <el-input v-model="newBot.welcome_message" placeholder="如：你好，我是物理小能手，问我任何物理问题！" maxlength="200" clearable />
        </el-form-item>
        <el-form-item label="推荐问题（每行一个）">
          <el-input
            v-model="newBot.suggested_text"
            type="textarea"
            :rows="3"
            placeholder="展示在聊天窗口的快捷提问，如：&#10;牛顿第二定律是什么？&#10;光的折射怎么理解？"
            resize="none"
          />
        </el-form-item>
        <el-form-item label="绑定知识库（可稍后配置）">
          <el-select v-model="newBot.kb_ids" multiple placeholder="选择知识库" style="width: 100%">
            <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createBot">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const bots = ref([])
const kbs = ref([])
const showCreate = ref(false)
const aiLoading = ref(false)
const newBot = ref({
  name: '',
  system_prompt: '',
  welcome_message: '',
  suggested_text: '',
  kb_ids: [],
  style: 'friendly',
})

async function aiPersona() {
  if (!newBot.value.name.trim()) {
    ElMessage.warning('请先输入智能体名称，AI 才能进行分析')
    return
  }
  aiLoading.value = true
  try {
    const kbNames = kbs.value
      .filter((kb) => newBot.value.kb_ids.includes(kb.id))
      .map((kb) => kb.name)
    const res = await api.post(
      '/api/ai/agent-profile',
      {
        name: newBot.value.name.trim(),
        kb_names: kbNames,
        style: newBot.value.style,
      },
      { timeout: 120000 }
    )
    const d = res.data
    if (d.system_prompt) newBot.value.system_prompt = d.system_prompt
    if (d.welcome_message) newBot.value.welcome_message = d.welcome_message
    if (d.suggested_questions?.length) {
      newBot.value.suggested_text = d.suggested_questions.join('\n')
    }
    ElMessage.success('AI 已生成完整配置，可自行微调')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || 'AI 生成失败，请稍后重试')
  } finally {
    aiLoading.value = false
  }
}

async function loadBots() {
  const res = await api.get('/api/bots')
  bots.value = res.data
}

async function loadKbs() {
  const res = await api.get('/api/kb')
  kbs.value = res.data
}

async function createBot() {
  if (!newBot.value.name.trim()) {
    ElMessage.warning('请输入智能体名称')
    return
  }
  try {
    const suggested = newBot.value.suggested_text
      .split('\n')
      .map((q) => q.trim())
      .filter(Boolean)
    await api.post('/api/bots', {
      name: newBot.value.name,
      system_prompt: newBot.value.system_prompt,
      welcome_message: newBot.value.welcome_message,
      suggested_questions: suggested,
      kb_ids: newBot.value.kb_ids,
    })
    ElMessage.success('创建成功')
    showCreate.value = false
    newBot.value = {
      name: '',
      system_prompt: '',
      welcome_message: '',
      suggested_text: '',
      kb_ids: [],
      style: newBot.value.style,
    }
    await loadBots()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  }
}

async function handleCommand(cmd, bot) {
  if (cmd === 'publish') {
    try {
      const res = await api.post(`/api/bots/${bot.id}/publish`)
      ElMessage.success('发布成功')
      bot.is_published = true
      bot.publish_token = res.data.publish_token
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '发布失败')
    }
  } else if (cmd === 'unpublish') {
    await api.post(`/api/bots/${bot.id}/unpublish`)
    ElMessage.success('已下线')
    bot.is_published = false
  } else if (cmd === 'link') {
    const url = `${window.location.origin}/chat/${bot.publish_token}`
    await navigator.clipboard.writeText(url)
    ElMessage.success('公开链接已复制到剪贴板')
  } else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(
        `删除智能体「${bot.name}」将同时删除其对话记录，不可恢复`,
        '危险操作',
        { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
      )
      await api.delete(`/api/bots/${bot.id}`)
      ElMessage.success('已删除')
      await loadBots()
    } catch {
      /* cancel */
    }
  }
}

onMounted(() => {
  loadBots()
  loadKbs()
})
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

.bot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.new-bot-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 190px;
  border: 1.5px dashed #f5cd6f;
  cursor: pointer;
  transition: all 0.2s;
  background: #fffdf5;
}

.new-bot-card:hover {
  border-color: #f5a623;
  background: #fdf8ec;
  transform: translateY(-2px);
}

.new-bot-text {
  color: #d48806;
  font-weight: 600;
  font-size: 15px;
}

.bot-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bot-card-head {
  display: flex;
  gap: 12px;
}

.bot-avatar {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mini-sunflower {
  width: 30px;
  height: 30px;
}

.bot-card-title {
  flex: 1;
  min-width: 0;
}

.bot-name {
  font-size: 17px;
  font-weight: 700;
}

.bot-prompt {
  font-size: 12px;
  color: #9aa3af;
  margin-top: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bot-meta {
  display: flex;
  gap: 8px;
}

.bot-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f5f2ea;
  padding-top: 10px;
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
