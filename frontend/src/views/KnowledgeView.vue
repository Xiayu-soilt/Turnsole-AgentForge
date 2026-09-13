<template>
  <div>
    <div class="page-header">
      <div class="page-title">知识库</div>
      <div class="page-desc">上传企业文档，构建智能体的大脑（支持 PDF / Word / Markdown / TXT）</div>
    </div>

    <div class="kb-layout">
      <div class="kb-list">
        <el-button class="new-kb-btn" size="large" @click="openCreate()">
          <el-icon><Plus /></el-icon>&nbsp;新建知识库
        </el-button>
        <el-button class="template-kb-btn" size="large" @click="showTemplates = true">
          <el-icon><MagicStick /></el-icon>&nbsp;模板市场
        </el-button>

        <div v-if="kbs.length === 0" class="kb-empty">
          还没有知识库<br />
          <span class="kb-empty-hint">试试点击上方「模板市场」，一键使用现成知识库</span>
        </div>

        <div
          v-for="kb in kbs"
          :key="kb.id"
          class="kb-card"
          :class="{ active: kb.id === activeKbId }"
          @click="selectKb(kb.id)"
        >
          <div class="kb-card-head">
            <el-icon class="kb-icon"><Collection /></el-icon>
            <div class="kb-card-title" :title="kb.name">{{ kb.name }}</div>
            <el-dropdown trigger="click" @command="handleKbCommand($event, kb)">
              <el-icon class="kb-more"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="delete" style="color: #f56c6c">
                    <el-icon><Delete /></el-icon>&nbsp;删除知识库
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div class="kb-card-desc">{{ kb.description || '暂无描述' }}</div>
          <div class="kb-card-stats">
            <span>{{ kb.doc_count }} 文档</span>
            <span>{{ kb.chunk_count }} 切片</span>
          </div>
        </div>
      </div>

      <div class="doc-panel card">
        <template v-if="activeKb">
          <div class="doc-head">
            <div>
              <div class="doc-title">{{ activeKb.name }}</div>
              <div class="doc-sub">{{ activeKb.description }}</div>
            </div>
            <div class="doc-head-actions">
              <el-button size="large" class="ai-doc-btn" @click="showAiDoc = true">
                <el-icon><MagicStick /></el-icon>&nbsp;AI 生成文档
              </el-button>
              <el-upload
                :show-file-list="false"
                :http-request="customUpload"
                :accept="'.pdf,.docx,.doc,.md,.txt,.csv,.log'"
                multiple
              >
                <el-button type="primary" size="large" class="upload-btn">
                  <el-icon><UploadFilled /></el-icon>&nbsp;上传文档
                </el-button>
              </el-upload>
            </div>
          </div>

          <el-alert
            v-if="docs.length === 0"
            title="这个知识库还没有文档，智能体会因检索不到内容而无法回答。试试右上角「AI 生成文档」，一键填充种子知识。"
            type="warning"
            :closable="false"
            class="ingest-tip"
          />

          <el-alert
            v-if="hasProcessing"
            title="文档正在解析与向量化，请稍候..."
            type="info"
            :closable="false"
            class="ingest-tip"
          />

          <el-table :data="docs" style="width: 100%" v-loading="docsLoading">
            <el-table-column label="文件名" min-width="220">
              <template #default="{ row }">
                <div class="doc-name">
                  <el-icon :size="18" :color="fileIconColor(row.file_type)">
                    <Document />
                  </el-icon>
                  <span>{{ row.filename }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="file_type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small" effect="plain" round>{{ row.file_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="大小" width="100">
              <template #default="{ row }">{{ formatSize(row.size) }}</template>
            </el-table-column>
            <el-table-column label="切片数" width="90">
              <template #default="{ row }">
                <span class="chunk-count">{{ row.chunk_count || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'done'" type="success" size="small" round>
                  已入库
                </el-tag>
                <el-tag v-else-if="row.status === 'processing'" type="warning" size="small" round>
                  处理中
                </el-tag>
                <el-tag v-else-if="row.status === 'pending'" size="small" round>
                  排队中
                </el-tag>
                <el-tooltip v-else :content="row.error || '处理失败'" placement="top">
                  <el-tag type="danger" size="small" round>失败</el-tag>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'failed'"
                  size="small"
                  text
                  type="primary"
                  @click="retryDoc(row)"
                >
                  重试
                </el-button>
                <el-popconfirm title="确定删除该文档吗？" @confirm="deleteDoc(row)">
                  <template #reference>
                    <el-button size="small" text type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无文档，点击右上角上传" :image-size="80" />
            </template>
          </el-table>
        </template>

        <div v-else class="tpl-showcase">
          <div class="tpl-showcase-head">
            <div>
              <div class="tpl-showcase-title">
                <span class="gradient-text">从模板开始</span>
                <el-tag size="small" effect="dark" round class="tpl-count-tag">
                  {{ KB_TEMPLATES.length }} 个现成模板
                </el-tag>
              </div>
              <div class="tpl-showcase-sub">
                精选企业高频场景，点击即用；也可以
                <el-link type="primary" :underline="false" @click="openCreate()">从零创建</el-link>
              </div>
            </div>
          </div>
          <div class="tpl-grid">
            <div
              v-for="tpl in KB_TEMPLATES"
              :key="tpl.name"
              class="tpl-card"
              @click="useTemplate(tpl)"
            >
              <div class="tpl-icon" :style="{ background: tpl.color }">
                <el-icon :size="20"><component :is="tpl.icon" /></el-icon>
              </div>
              <div class="tpl-name">{{ tpl.name }}</div>
              <div class="tpl-desc">{{ tpl.description }}</div>
              <div class="tpl-docs">
                <el-tag v-for="d in tpl.docs" :key="d" size="small" effect="plain" round>
                  {{ d }}
                </el-tag>
              </div>
              <div class="tpl-use">使用模板 →</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showTemplates" title="模板市场" width="860px" class="tpl-dialog">
      <div class="tpl-dialog-sub">选择一个场景模板，快速创建属于你的知识库</div>
      <div class="tpl-grid tpl-grid-dialog">
        <div v-for="tpl in KB_TEMPLATES" :key="tpl.name" class="tpl-card" @click="useTemplate(tpl)">
          <div class="tpl-icon" :style="{ background: tpl.color }">
            <el-icon :size="20"><component :is="tpl.icon" /></el-icon>
          </div>
          <div class="tpl-name">{{ tpl.name }}</div>
          <div class="tpl-desc">{{ tpl.description }}</div>
          <div class="tpl-docs">
            <el-tag v-for="d in tpl.docs" :key="d" size="small" effect="plain" round>
              {{ d }}
            </el-tag>
          </div>
          <div class="tpl-use">使用模板 →</div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showAiDoc" title="AI 生成知识文档" width="620px" class="ai-doc-dialog">
      <div class="ai-doc-tip">
        输入主题，AI 将为「{{ activeKb?.name }}」撰写一篇结构化知识文档，生成后自动切片入库
      </div>
      <el-form label-position="top" size="large">
        <el-form-item label="文档主题" required>
          <el-input
            v-model="aiDoc.topic"
            placeholder="如：牛顿运动定律、报销流程、光的三原色"
            maxlength="200"
            clearable
          />
        </el-form-item>
        <el-form-item label="文档风格">
          <el-radio-group v-model="aiDoc.style">
            <el-radio-button value="tutorial">教学讲解</el-radio-button>
            <el-radio-button value="handbook">制度手册</el-radio-button>
            <el-radio-button value="faq">FAQ 问答</el-radio-button>
            <el-radio-button value="science">科普文章</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容要点（可选）">
          <el-input
            v-model="aiDoc.points"
            type="textarea"
            :rows="2"
            placeholder="希望覆盖的要点，用逗号分隔，如：三大定律、惯性、单位换算"
            resize="none"
          />
        </el-form-item>
      </el-form>

      <div v-if="aiDoc.content" class="ai-doc-preview">
        <div class="ai-doc-preview-title">
          <el-icon color="#d48806"><Document /></el-icon>
          <span>{{ aiDoc.title }}</span>
        </div>
        <pre class="ai-doc-preview-body">{{ aiDoc.content }}</pre>
      </div>

      <template #footer>
        <el-button v-if="aiDoc.content" @click="aiDoc.content = ''">重新编辑参数</el-button>
        <el-button class="ai-gen-btn-lg" :loading="aiDocLoading" @click="generateDoc">
          {{ aiDoc.content ? '重新生成' : 'AI 生成' }}
        </el-button>
        <el-button
          v-if="aiDoc.content"
          type="primary"
          :loading="aiDocSaving"
          @click="saveAiDoc"
        >
          保存入库
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreate" title="新建知识库" width="480px">
      <el-form label-position="top" size="large">
        <el-form-item label="知识库名称" required>
          <el-input
            v-model="newKb.name"
            placeholder="如：产品手册、公司制度、客服 FAQ"
            maxlength="100"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <template #label>
            <div class="ai-label-row">
              <span>描述</span>
              <div class="ai-label-controls">
                <el-select v-model="newKb.style" size="small" class="style-select">
                  <el-option value="concise" label="专业简洁" />
                  <el-option value="detailed" label="详细丰富" />
                  <el-option value="lively" label="活泼生动" />
                </el-select>
                <el-button
                  class="ai-gen-btn"
                  size="small"
                  :loading="aiLoading"
                  @click="aiDescribe"
                >
                  <el-icon v-if="!aiLoading"><MagicStick /></el-icon>&nbsp;AI 智能生成
                </el-button>
              </div>
            </div>
          </template>
          <el-input
            v-model="newKb.description"
            type="textarea"
            :rows="3"
            placeholder="简单说明知识库内容，也可以让 AI 根据名称自动生成"
            resize="none"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createKb">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, markRaw } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Box,
  Collection,
  Delete,
  Document,
  FirstAidKit,
  Guide,
  MagicStick,
  Monitor,
  MoreFilled,
  OfficeBuilding,
  Plus,
  Reading,
  Service,
  ShoppingCart,
  Stamp,
  TrendCharts,
  UploadFilled,
  User,
  Wallet,
} from '@element-plus/icons-vue'
import api from '../api'

const KB_TEMPLATES = [
  {
    name: '产品手册',
    description: '产品功能说明、操作指引与版本更新，让智能体秒变产品专家',
    docs: ['功能说明', '操作手册', '更新日志'],
    icon: markRaw(Box),
    color: 'linear-gradient(135deg, #f7b733, #f59f00)',
  },
  {
    name: '客服 FAQ',
    description: '高频问题与售后政策，7×24 小时自动应答客户咨询',
    docs: ['常见问题', '售后政策', '退换流程'],
    icon: markRaw(Service),
    color: 'linear-gradient(135deg, #ff9800, #f56419)',
  },
  {
    name: 'HR 制度',
    description: '员工手册、考勤假期、薪酬福利，员工问人效不如问智能体',
    docs: ['员工手册', '考勤假期', '薪酬福利'],
    icon: markRaw(User),
    color: 'linear-gradient(135deg, #8bc34a, #558b2f)',
  },
  {
    name: 'IT 支持',
    description: '运维手册与故障排查指南，IT 工单量直接减半',
    docs: ['运维手册', '故障排查', '账号权限'],
    icon: markRaw(Monitor),
    color: 'linear-gradient(135deg, #4fc3f7, #0288d1)',
  },
  {
    name: '销售话术',
    description: '产品卖点、异议处理与报价策略，新人也能快速开单',
    docs: ['产品卖点', '异议处理', '报价策略'],
    icon: markRaw(TrendCharts),
    color: 'linear-gradient(135deg, #ffca28, #ff9800)',
  },
  {
    name: '法务合同',
    description: '合同模板与合规审查要点，业务侧自助查询不出错',
    docs: ['合同模板', '合规要求', '审查要点'],
    icon: markRaw(Stamp),
    color: 'linear-gradient(135deg, #b39ddb, #7e57c2)',
  },
  {
    name: '财务报销',
    description: '报销流程、发票规范与预算制度，告别重复答疑',
    docs: ['报销流程', '发票规范', '预算制度'],
    icon: markRaw(Wallet),
    color: 'linear-gradient(135deg, #26a69a, #00897b)',
  },
  {
    name: '培训资料',
    description: '课程讲义与学习路径，企业内训知识一网打尽',
    docs: ['课程讲义', '学习路径', '考核标准'],
    icon: markRaw(Reading),
    color: 'linear-gradient(135deg, #ff8a65, #ff7043)',
  },
  {
    name: '电商运营',
    description: '商品信息、活动规则与物流说明，大促咨询不炸客服',
    docs: ['商品信息', '活动规则', '物流说明'],
    icon: markRaw(ShoppingCart),
    color: 'linear-gradient(135deg, #ffb300, #ff8f3d)',
  },
  {
    name: '物业服务',
    description: '楼宇设施、缴费指南与报修流程，业主满意度提升利器',
    docs: ['楼宇设施', '缴费指南', '报修流程'],
    icon: markRaw(OfficeBuilding),
    color: 'linear-gradient(135deg, #64b5f6, #1976d2)',
  },
  {
    name: '医疗健康',
    description: '科室介绍、就诊流程与健康科普，导诊分流更高效',
    docs: ['科室介绍', '就诊流程', '健康科普'],
    icon: markRaw(FirstAidKit),
    color: 'linear-gradient(135deg, #ef5350, #e53935)',
  },
  {
    name: '政务服务',
    description: '办事指南、材料清单与政策解读，窗口咨询前移线上',
    docs: ['办事指南', '材料清单', '政策解读'],
    icon: markRaw(Guide),
    color: 'linear-gradient(135deg, #7986cb, #3f51b5)',
  },
]

const kbs = ref([])
const docs = ref([])
const activeKbId = ref(null)
const docsLoading = ref(false)
const showCreate = ref(false)
const showTemplates = ref(false)
const showAiDoc = ref(false)
const aiLoading = ref(false)
const aiDocLoading = ref(false)
const aiDocSaving = ref(false)
const aiDoc = ref({ topic: '', style: 'tutorial', points: '', title: '', content: '' })
const newKb = ref({ name: '', description: '', style: 'concise' })
let pollTimer = null

const activeKb = computed(() => kbs.value.find((k) => k.id === activeKbId.value) || null)
const hasProcessing = computed(() =>
  docs.value.some((d) => d.status === 'pending' || d.status === 'processing')
)

async function loadKbs() {
  const res = await api.get('/api/kb')
  kbs.value = res.data
  if (!activeKbId.value && kbs.value.length > 0) {
    activeKbId.value = kbs.value[0].id
  }
  if (activeKbId.value) {
    await loadDocs()
  }
}

async function loadDocs() {
  if (!activeKbId.value) return
  docsLoading.value = true
  try {
    const res = await api.get(`/api/kb/${activeKbId.value}/docs`)
    docs.value = res.data
    schedulePoll()
  } finally {
    docsLoading.value = false
  }
}

function schedulePoll() {
  if (pollTimer) clearTimeout(pollTimer)
  if (hasProcessing.value) {
    pollTimer = setTimeout(async () => {
      await loadDocs()
      await loadKbStats()
    }, 3000)
  }
}

async function loadKbStats() {
  const res = await api.get('/api/kb')
  kbs.value = res.data
}

function selectKb(id) {
  activeKbId.value = id
  loadDocs()
}

function openCreate(prefill = { name: '', description: '' }) {
  newKb.value = {
    name: prefill.name,
    description: prefill.description,
    style: newKb.value?.style || 'concise',
  }
  showCreate.value = true
}

function useTemplate(tpl) {
  showTemplates.value = false
  openCreate({ name: tpl.name, description: tpl.description })
}

async function aiDescribe() {
  if (!newKb.value.name.trim()) {
    ElMessage.warning('请先输入知识库名称，AI 才能进行分析')
    return
  }
  aiLoading.value = true
  try {
    const res = await api.post(
      '/api/ai/kb-description',
      {
        name: newKb.value.name.trim(),
        style: newKb.value.style || 'concise',
      },
      { timeout: 120000 }
    )
    if (res.data.description) {
      newKb.value.description = res.data.description
      ElMessage.success('AI 已生成描述，可自行修改')
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || 'AI 生成失败，请稍后重试')
  } finally {
    aiLoading.value = false
  }
}

async function generateDoc() {
  if (!aiDoc.value.topic.trim()) {
    ElMessage.warning('请先输入文档主题')
    return
  }
  aiDocLoading.value = true
  try {
    const res = await api.post(
      '/api/ai/generate-doc',
      {
        topic: aiDoc.value.topic.trim(),
        kb_name: activeKb.value?.name || '',
        style: aiDoc.value.style,
        points: aiDoc.value.points,
      },
      { timeout: 180000 }
    )
    if (res.data.content) {
      aiDoc.value.content = res.data.content
      aiDoc.value.title = res.data.title
      ElMessage.success('AI 已生成文档，确认无误后保存入库')
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || 'AI 生成失败，请稍后重试')
  } finally {
    aiDocLoading.value = false
  }
}

async function saveAiDoc() {
  aiDocSaving.value = true
  try {
    await api.post(`/api/kb/${activeKbId.value}/docs/ai`, {
      title: aiDoc.value.title,
      content: aiDoc.value.content,
    })
    ElMessage.success('已入库，正在切片与向量化')
    showAiDoc.value = false
    aiDoc.value = { topic: '', style: 'tutorial', points: '', title: '', content: '' }
    await loadDocs()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    aiDocSaving.value = false
  }
}

async function createKb() {
  if (!newKb.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  try {
    const res = await api.post('/api/kb', newKb.value)
    ElMessage.success('创建成功')
    showCreate.value = false
    newKb.value = { name: '', description: '' }
    await loadKbs()
    activeKbId.value = res.data.id
    await loadDocs()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  }
}

async function handleKbCommand(cmd, kb) {
  if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(
        `删除知识库「${kb.name}」将同时删除其所有文档与向量数据，不可恢复`,
        '危险操作',
        { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
      )
      await api.delete(`/api/kb/${kb.id}`)
      ElMessage.success('已删除')
      if (activeKbId.value === kb.id) {
        activeKbId.value = null
        docs.value = []
      }
      await loadKbs()
    } catch {
      /* cancel */
    }
  }
}

async function customUpload(options) {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    await api.post(`/api/kb/${activeKbId.value}/docs`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success(`「${options.file.name}」上传成功，开始处理`)
    await loadDocs()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || `「${options.file.name}」上传失败`)
  }
}

async function deleteDoc(row) {
  try {
    await api.delete(`/api/kb/${activeKbId.value}/docs/${row.id}`)
    ElMessage.success('已删除')
    await loadDocs()
    await loadKbStats()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

async function retryDoc(row) {
  try {
    await api.post(`/api/kb/${activeKbId.value}/docs/${row.id}/retry`)
    ElMessage.success('已重新加入处理队列')
    await loadDocs()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '重试失败')
  }
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function fileIconColor(type) {
  if (type === 'pdf') return '#f56c6c'
  if (['docx', 'doc'].includes(type)) return '#409eff'
  return '#f5a623'
}

loadKbs()

onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
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

.kb-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  align-items: start;
}

.kb-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.new-kb-btn {
  width: 100%;
  border: none;
  color: #fff;
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 12px;
  box-shadow: 0 4px 14px rgba(245, 166, 35, 0.3);
}

.new-kb-btn:hover {
  color: #fff;
  background: linear-gradient(135deg, #ffd25e, #f7ae2e);
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(245, 166, 35, 0.38);
}

.template-kb-btn {
  width: 100%;
  border: 1px solid #ffe3a6;
  color: #d48806;
  background: #fffaf0;
  height: 44px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 12px;
}

.template-kb-btn:hover {
  color: #d48806;
  border-color: #f8d9a0;
  background: #fdf3dd;
}

.kb-empty {
  text-align: center;
  color: #a8b0bd;
  font-size: 13px;
  padding: 20px 0;
  line-height: 1.8;
}

.kb-empty-hint {
  color: #c4c9d4;
  font-size: 12px;
}

.kb-card {
  background: #fff;
  border: 1.5px solid transparent;
  border-radius: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.kb-card:hover {
  border-color: #ffdfae;
}

.kb-card.active {
  border-color: #f5a623;
  background: linear-gradient(135deg, #fffaf0, #fff);
  box-shadow: 0 4px 16px rgba(245, 166, 35, 0.14);
}

.kb-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kb-icon {
  color: #f5a623;
  font-size: 18px;
}

.kb-card-title {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-more {
  color: #c4c9d4;
  cursor: pointer;
}

.kb-more:hover {
  color: #8a919e;
}

.kb-card-desc {
  font-size: 12px;
  color: #9aa3af;
  margin: 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-card-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #f5a623;
  font-weight: 600;
}

.doc-panel {
  min-height: 480px;
}

.doc-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.doc-title {
  font-size: 18px;
  font-weight: 700;
}

.doc-sub {
  font-size: 13px;
  color: #9aa3af;
  margin-top: 2px;
}

.upload-btn {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  border: none;
  border-radius: 10px;
}

.ingest-tip {
  margin-bottom: 12px;
}

.doc-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chunk-count {
  font-weight: 700;
  color: #f5a623;
}

/* ---------- 模板市场 ---------- */

.tpl-showcase-head {
  margin-bottom: 18px;
}

.tpl-showcase-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 700;
}

.tpl-count-tag {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  border: none;
  color: #fff;
  font-weight: 600;
}

.tpl-showcase-sub {
  color: #8a919e;
  font-size: 14px;
  margin-top: 6px;
}

.tpl-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}

.tpl-grid-dialog {
  max-height: 58vh;
  overflow-y: auto;
  padding-right: 6px;
}

.tpl-dialog-sub {
  color: #8a919e;
  font-size: 13px;
  margin: -6px 0 16px;
}

.tpl-card {
  border: 1px solid #f2ecdc;
  border-radius: 14px;
  padding: 18px 16px 14px;
  cursor: pointer;
  transition: all 0.22s ease;
  background: #fffdf5;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tpl-card:hover {
  border-color: #f5cd6f;
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(245, 166, 35, 0.18);
}

.tpl-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.tpl-name {
  font-size: 15px;
  font-weight: 700;
  margin-top: 2px;
}

.tpl-desc {
  font-size: 12px;
  color: #9aa3af;
  line-height: 1.6;
  min-height: 38px;
}

.tpl-docs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tpl-use {
  font-size: 13px;
  font-weight: 600;
  color: #d48806;
  margin-top: auto;
  padding-top: 6px;
}

/* ---------- AI 生成 ---------- */

.doc-head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.ai-doc-btn {
  border: 1px solid #f5cd6f;
  color: #d48806;
  background: #fffdf5;
  border-radius: 10px;
  font-weight: 600;
}

.ai-doc-btn:hover {
  color: #c4881d;
  border-color: #f5a623;
  background: #fdf3dd;
}

.ai-doc-tip {
  font-size: 13px;
  color: #8a919e;
  background: #fdf8ec;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
}

.ai-doc-preview {
  border: 1px solid #f2ecdc;
  border-radius: 12px;
  margin-top: 4px;
  overflow: hidden;
}

.ai-doc-preview-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 15px;
  padding: 12px 16px;
  background: #fdf8ec;
  border-bottom: 1px solid #f2ecdc;
}

.ai-doc-preview-body {
  max-height: 280px;
  overflow-y: auto;
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  color: #4a5060;
}

.ai-gen-btn-lg {
  color: #d48806;
  border-color: #f5cd6f;
  font-weight: 600;
}

.ai-gen-btn-lg:hover {
  color: #c4881d;
  border-color: #f5a623;
  background: #fdf3dd;
}

.ai-label-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.style-select {
  width: 108px;
}

.ai-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 4px;
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
