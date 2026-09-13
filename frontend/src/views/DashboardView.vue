<template>
  <div>
    <div class="page-header">
      <div class="page-title">数据看板</div>
      <div class="page-desc">掌握智能体的运行情况与知识库健康度</div>
    </div>

    <div class="stat-grid">
      <div class="card stat-card">
        <div class="stat-label"><el-icon><ChatDotRound /></el-icon> 会话总数</div>
        <div class="stat-value gradient-text">{{ stats.total_conversations }}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label"><el-icon><Message /></el-icon> 提问总数</div>
        <div class="stat-value">{{ stats.total_user_messages }}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label"><el-icon><CaretTop /></el-icon> 点赞 / 点踩</div>
        <div class="stat-value">
          <span style="color: #d48806">{{ stats.total_likes }}</span>
          <span style="color: #c4c9d4; font-size: 18px; margin: 0 6px">/</span>
          <span style="color: #8a919e; font-size: 22px">{{ stats.total_dislikes }}</span>
        </div>
      </div>
      <div class="card stat-card">
        <div class="stat-label"><el-icon><Aim /></el-icon> 检索命中率</div>
        <div class="stat-value">{{ (stats.hit_rate * 100).toFixed(1) }}%</div>
      </div>
    </div>

    <div class="main-grid">
      <div class="card chart-card">
        <div class="chart-title">近 14 天提问量趋势</div>
        <div ref="trendChartRef" class="chart-box"></div>
      </div>
      <div class="card hot-card">
        <div class="chart-title">热门问题 TOP10</div>
        <div v-if="stats.hot_questions.length === 0" class="empty-tip">暂无数据</div>
        <div v-else class="hot-list">
          <div v-for="(item, i) in stats.hot_questions" :key="i" class="hot-item">
            <span class="hot-rank" :class="{ top: i < 3 }">{{ i + 1 }}</span>
            <span class="hot-question">{{ item.question }}</span>
            <el-tag size="small" type="danger" effect="plain" round>{{ item.count }} 次</el-tag>
          </div>
        </div>
      </div>
    </div>

    <div class="resource-grid">
      <div class="card res-card">
        <el-icon class="res-icon" color="#f5a623"><Collection /></el-icon>
        <div class="res-info">
          <div class="res-value">{{ stats.kb_count }}</div>
          <div class="res-label">知识库</div>
        </div>
      </div>
      <div class="card res-card">
        <el-icon class="res-icon" color="#d48806"><Document /></el-icon>
        <div class="res-info">
          <div class="res-value">{{ stats.doc_count }}</div>
          <div class="res-label">已入库文档</div>
        </div>
      </div>
      <div class="card res-card">
        <el-icon class="res-icon" color="#f7b733"><Grid /></el-icon>
        <div class="res-info">
          <div class="res-value">{{ stats.chunk_count }}</div>
          <div class="res-label">知识切片</div>
        </div>
      </div>
      <div class="card res-card">
        <el-icon class="res-icon" color="#ffc44a"><Service /></el-icon>
        <div class="res-info">
          <div class="res-value">{{ stats.bot_count }}</div>
          <div class="res-label">智能体</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import api from '../api'

const stats = ref({
  total_conversations: 0,
  total_messages: 0,
  total_user_messages: 0,
  total_likes: 0,
  total_dislikes: 0,
  hit_rate: 0,
  doc_count: 0,
  chunk_count: 0,
  bot_count: 0,
  kb_count: 0,
  daily: [],
  hot_questions: [],
})

const trendChartRef = ref(null)
let chartInstance = null

async function loadStats() {
  try {
    const res = await api.get('/api/stats')
    stats.value = res.data
    renderTrend()
  } catch {
    /* empty */
  }
}

function renderTrend() {
  if (!trendChartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(trendChartRef.value)
  }
  const daily = stats.value.daily || []
  chartInstance.setOption({
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: daily.map((d) => d.date.slice(5)),
      axisLine: { lineStyle: { color: '#d3d6de' } },
      axisLabel: { color: '#8a919e' },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f1f5' } },
      axisLabel: { color: '#8a919e' },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        data: daily.map((d) => d.count),
        lineStyle: {
          width: 3,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#ffc53d' },
            { offset: 1, color: '#f5a623' },
          ]),
        },
        itemStyle: { color: '#f5a623' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245, 166, 35, 0.25)' },
            { offset: 1, color: 'rgba(245, 166, 35, 0)' },
          ]),
        },
      },
    ],
  })
}

function handleResize() {
  chartInstance && chartInstance.resize()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance && chartInstance.dispose()
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

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  padding: 20px 24px;
}

.stat-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #8a919e;
  font-size: 14px;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: #2c3038;
}

.main-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.chart-card {
  min-height: 320px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.chart-box {
  height: 260px;
}

.hot-card {
  min-height: 320px;
}

.empty-tip {
  text-align: center;
  color: #c4c9d4;
  padding: 80px 0;
}

.hot-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #fafbfc;
}

.hot-rank {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #f0f1f5;
  color: #8a919e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.hot-rank.top {
  background: linear-gradient(135deg, #ffc53d, #f5a623);
  color: #fff;
}

.hot-question {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.res-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 24px;
}

.res-icon {
  font-size: 34px;
}

.res-value {
  font-size: 26px;
  font-weight: 800;
}

.res-label {
  color: #8a919e;
  font-size: 13px;
}
</style>
