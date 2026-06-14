<template>
  <div class="dashboard-mobile">
    <!-- 空状态 -->
    <div v-if="!authStore.currentPatient" class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>请先选择患者</h3>
      <p>在顶部选择或添加患者以查看健康数据</p>
      <el-button type="primary" size="large" round @click="router.push('/patients')">
        <el-icon style="margin-right:6px;"><User /></el-icon>
        管理患者
      </el-button>
    </div>

    <template v-else>
      <!-- 用药卡片 -->
      <div v-if="dashboard.medication_compare" class="med-card">
        <div class="med-header">
          <div>
            <span class="med-title">最新用药</span>
            <el-tag size="small" round style="margin-left:8px;">{{ dashboard.medication_compare.doctor }}</el-tag>
          </div>
          <span class="med-date">{{ dashboard.medication_compare.created_at?.slice(0, 10) }}</span>
        </div>
        <div class="med-list">
          <div v-for="(item, idx) in dashboard.medication_compare.drugs" :key="idx" class="med-item">
            <div class="med-item-content">
              <span class="med-name">{{ item.drug_name }}</span>
              <span class="med-dot">·</span>
              <span class="med-spec">{{ item.specification }}</span>
              <span class="med-dot">·</span>
              <span class="med-dosage">{{ item.dosage }}</span>
              <span class="med-dot">·</span>
              <span class="med-usage">{{ item.usage_method }}</span>
            </div>
            <el-tag 
              :type="item.status === 'new' ? 'success' : item.status === 'changed' ? 'warning' : item.status === 'removed' ? 'danger' : 'info'"
              size="small"
              round
            >
              {{ item.status === 'new' ? '新增' : item.status === 'changed' ? '变更' : item.status === 'removed' ? '停用' : '不变' }}
            </el-tag>
          </div>
        </div>
        <el-button v-if="hasChanges" type="primary" link size="small" @click="showPrevDetail = true">
          查看上次用药详情 →
        </el-button>
      </div>

      <!-- 核心指标卡片 -->
      <div class="stats-grid">
        <div class="stat-card gradient-red" @click="scrollToAnomaly">
          <div class="stat-header">
            <span class="stat-icon">⚠️</span>
            <span class="stat-label">异常指标</span>
          </div>
          <div class="stat-value" :class="totalAnomalies > 0 ? 'text-danger' : 'text-success'">{{ totalAnomalies }}</div>
        </div>
        <div class="stat-card gradient-orange" @click="scrollToWatch">
          <div class="stat-header">
            <span class="stat-icon">📊</span>
            <span class="stat-label">需关注</span>
          </div>
          <div class="stat-value" :class="dashboard.watch_list.length > 0 ? 'text-warning' : 'text-success'">{{ dashboard.watch_list.length }}</div>
        </div>
        <div class="stat-card gradient-blue" @click="openLatestReport">
          <div class="stat-header">
            <span class="stat-icon">📅</span>
            <span class="stat-label">最新检查</span>
          </div>
          <div class="stat-value-date">{{ dashboard.latest_report?.exam_date || '-' }}</div>
        </div>
        <div class="stat-card gradient-green" @click="router.push('/reports')">
          <div class="stat-header">
            <span class="stat-icon">📋</span>
            <span class="stat-label">报告库</span>
          </div>
          <div class="stat-value">{{ totalReports }}</div>
        </div>
      </div>

      <!-- 异常指标详细列表 -->
      <el-card id="anomaly-section" class="section-card anomaly-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div style="display:flex;align-items:center;gap:6px;">
              <el-icon color="#f5576c"><WarningFilled /></el-icon>
              <span class="card-title">异常指标详情</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <el-input
                v-model="anomalySearch"
                placeholder="搜索指标/类别..."
                size="small"
                clearable
                style="width:140px;"
                :prefix-icon="SearchIcon"
              />
              <span class="card-hint" style="font-size:11px;">近 1 年</span>
            </div>
          </div>
        </template>
        <div v-if="!dashboard.anomaly_details || filteredAnomalies.length === 0" class="empty-mini">
          <div class="empty-mini-icon">✅</div>
          <p>暂无异常指标</p>
        </div>
        <div v-else class="anomaly-detail-scroll">
          <div v-for="item in filteredAnomalies" :key="item.id + item.metric_name" class="anomaly-detail-item">
            <div class="anomaly-detail-row">
              <span class="detail-label">检查日期</span>
              <span class="detail-value">{{ item.exam_date }}</span>
            </div>
            <div class="anomaly-detail-row">
              <span class="detail-label">项目类别</span>
              <span class="detail-value">{{ item.institution }}</span>
            </div>
            <div class="anomaly-detail-row-main">
              <span class="detail-label">指标</span>
              <span class="detail-value">{{ item.metric_name }}</span>
              <span class="result-badge" :class="item.is_high ? 'high' : 'low'">
                {{ item.value }} {{ item.unit }}
                <el-tag :type="item.is_high ? 'danger' : 'warning'" size="small" round>
                  {{ item.is_high ? '偏高' : '偏低' }}
                </el-tag>
              </span>
            </div>
            <div class="anomaly-detail-row">
              <span class="detail-label">参考区间</span>
              <span class="detail-value">
                {{ item.ref_min != null && item.ref_max != null ? `${item.ref_min} ~ ${item.ref_max}` : item.ref_min != null ? `≥${item.ref_min}` : item.ref_max != null ? `≤${item.ref_max}` : '-' }}
              </span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 需关注趋势 -->
      <el-card id="watch-section" class="section-card watch-card" shadow="never" style="margin-top:16px;">
        <template #header>
          <div class="section-header">
            <div style="display:flex;align-items:center;gap:6px;">
              <el-icon color="#a6c1ee"><TrendCharts /></el-icon>
              <span class="card-title">需关注趋势</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <el-select
                v-model="watchSearch"
                placeholder="搜索指标"
                size="small"
                clearable
                filterable
                style="width:140px;"
              >
                <el-option
                  v-for="item in dashboard.watch_list"
                  :key="item.metric_name"
                  :label="item.metric_name"
                  :value="item.metric_name"
                />
              </el-select>
            </div>
          </div>
        </template>
        <div v-if="filteredWatchList.length > 0" class="watch-list">
          <div v-for="item in filteredWatchList" :key="item.metric_name" class="watch-item">
            <div class="watch-info">
              <div class="watch-name">{{ item.metric_name }}</div>
              <div class="watch-count" :class="item.direction === 'up' ? 'dir-up' : item.direction === 'down' ? 'dir-down' : ''">
                {{ item.warning }}
              </div>
            </div>
            <el-button size="small" round @click="goToTrend(item.metric_name)">
              查看趋势
            </el-button>
          </div>
        </div>
        <div v-else class="empty-mini">
          <div class="empty-mini-icon">🎉</div>
          <p>所有指标趋势正常</p>
        </div>
      </el-card>
    </template>

    <!-- 弹窗：上次用药详情 -->
    <el-dialog v-model="showPrevDetail" title="上次用药详情" class="mobile-dialog">
      <template v-if="prevDetail">
        <div class="med-detail">
          <div class="med-detail-header">
            <div class="med-detail-row">
              <span class="label">开药医生</span>
              <span class="value">{{ prevDetail.doctor }}</span>
            </div>
            <div class="med-detail-row">
              <span class="label">记录时间</span>
              <span class="value">{{ prevDetail.created_at?.slice(0, 16) }}</span>
            </div>
          </div>
          <div class="med-detail-list">
            <div v-for="(item, idx) in prevDetail.drugs" :key="idx" class="med-detail-item">
              <div class="med-detail-name">{{ item.drug_name }}</div>
              <div class="med-detail-spec">{{ item.specification }} · {{ item.dosage }}</div>
              <div class="med-detail-usage">{{ item.usage_method }}</div>
              <div v-if="item.notes" class="med-detail-notes">备注：{{ item.notes }}</div>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="empty-state-small">
        <p>上次无用药记录</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getDashboard } from '../api'
import { User, WarningFilled, TrendCharts, Search as SearchIcon } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const dashboard = ref<any>({
  patient_name: '',
  total_reports: 0,
  anomalies: [],
  anomaly_details: [],
  watch_list: [],
  latest_report: null,
  medication_compare: null,
})

const showPrevDetail = ref(false)
const prevDetail = ref<any>(null)
const anomalySearch = ref('')
const watchSearch = ref('')

const totalAnomalies = computed(() => dashboard.value.total_anomalies || 0)
const totalReports = computed(() => dashboard.value.total_reports || 0)
const hasChanges = computed(() => {
  return dashboard.value.medication_compare?.drugs?.some((d: any) => 
    ['new', 'changed', 'removed'].includes(d.status)
  )
})

const filteredAnomalies = computed(() => {
  const list = dashboard.value.anomaly_details || []
  const q = anomalySearch.value.toLowerCase()
  if (!q) return list
  return list.filter((item: any) =>
    item.metric_name.toLowerCase().includes(q) ||
    item.institution.toLowerCase().includes(q)
  )
})

const filteredWatchList = computed(() => {
  const list = dashboard.value.watch_list || []
  if (!watchSearch.value) return list
  return list.filter((item: any) => item.metric_name === watchSearch.value)
})

async function loadDashboard() {
  if (!authStore.currentPatient?.id) return
  const res = await getDashboard(authStore.currentPatient.id)
  dashboard.value = res.data
  if (res.data.medication_compare?.previous_record) {
    prevDetail.value = res.data.medication_compare.previous_record
  }
}

function openLatestReport() {
  const id = dashboard.value.latest_report?.id
  if (id) {
    router.push(`/reports?id=${id}`)
  }
}

function scrollToAnomaly() {
  const el = document.getElementById('anomaly-section')
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

function scrollToWatch() {
  const el = document.getElementById('watch-section')
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

function goToTrend(metricName: string) {
  router.push({ path: '/trend', query: { metric: metricName } })
}

watch(() => authStore.currentPatient, loadDashboard, { immediate: true })

onMounted(async () => {
  await loadDashboard()
})
</script>

<style scoped>
.dashboard-mobile {
  padding: 12px;
  padding-bottom: 80px;
  max-width: 600px;
  margin: 0 auto;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: var(--text);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 20px;
}

/* 用药卡片 */
.med-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  color: white;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.med-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.med-title {
  font-size: 16px;
  font-weight: 700;
}

.med-date {
  font-size: 12px;
  opacity: 0.9;
}

.med-list {
  margin-bottom: 12px;
}

.med-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  flex-wrap: nowrap;
}

.med-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.med-item-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
  overflow: hidden;
  margin-right: 8px;
}

.med-name {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.med-dot {
  font-size: 10px;
  opacity: 0.7;
  flex-shrink: 0;
}

.med-spec, .med-dosage, .med-usage {
  font-size: 11px;
  opacity: 0.85;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 0;
}

/* 指标卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 16px;
  padding: 16px;
  color: white;
  cursor: pointer;
  transition: transform 0.2s;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.stat-card:active {
  transform: scale(0.96);
}

.gradient-blue {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.gradient-red {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.gradient-orange {
  background: linear-gradient(135deg, #fbc2eb, #a6c1ee);
}

.gradient-green {
  background: linear-gradient(135deg, #84fab0, #8fd3f4);
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.stat-icon {
  font-size: 20px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-value-date {
  font-size: 16px;
  font-weight: 600;
}

.text-danger { color: #ffcdd2; }
.text-success { color: #c8e6c9; }
.text-warning { color: #fff9c4; }

/* 异常指标详细列表 */
.anomaly-detail-scroll {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.anomaly-detail-item {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.anomaly-detail-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
}

.anomaly-detail-row-main {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1 1 100%;
  min-width: 100%;
}

.detail-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.detail-value {
  font-size: 13px;
  color: var(--text);
  font-weight: 500;
}

.result-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  font-weight: 600;
  font-size: 14px;
}

.result-badge.high {
  color: #ef4444;
}

.result-badge.low {
  color: #f59e0b;
}

/* 区块卡片 */
.section-card {
  border-radius: 12px;
  margin-bottom: 16px;
  border: none;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.section-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: none;
  border-radius: 12px 12px 0 0;
}

.anomaly-card {
  background: linear-gradient(135deg, #fff5f7 0%, #fff0f3 100%);
}

.anomaly-card :deep(.el-card__header) {
  background: linear-gradient(135deg, rgba(245, 87, 108, 0.08), rgba(245, 87, 108, 0.02));
}

.watch-card {
  background: linear-gradient(135deg, #f5f7ff 0%, #f0f4ff 100%);
}

.watch-card :deep(.el-card__header) {
  background: linear-gradient(135deg, rgba(166, 193, 238, 0.1), rgba(166, 193, 238, 0.02));
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.card-hint {
  font-size: 11px;
  color: var(--text-secondary);
}

.chart-container {
  height: 260px;
}

.empty-mini {
  text-align: center;
  padding: 30px 0;
}

.empty-mini-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.empty-mini p {
  color: var(--text-secondary);
  font-size: 13px;
}

/* 关注列表 */
.watch-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.watch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.watch-item:last-child {
  border-bottom: none;
}

.watch-info {
  flex: 1;
}

.watch-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 4px;
}

.watch-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.watch-count.dir-up {
  color: #ef4444;
  font-weight: 600;
}

.watch-count.dir-down {
  color: #3b82f6;
  font-weight: 600;
}

/* 弹窗 */
.mobile-dialog :deep(.el-dialog__body) {
  padding: 16px;
}

.med-detail {
  padding: 8px 0;
}

.med-detail-header {
  margin-bottom: 16px;
}

.med-detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.med-detail-row .label {
  color: var(--text-secondary);
  font-size: 13px;
}

.med-detail-row .value {
  color: var(--text);
  font-size: 13px;
  font-weight: 500;
}

.med-detail-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.med-detail-item {
  background: #f8fafc;
  padding: 12px;
  border-radius: 10px;
}

.med-detail-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--primary);
}

.med-detail-spec, .med-detail-usage {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.med-detail-notes {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed #e0e0e0;
}

.empty-state-small {
  text-align: center;
  padding: 30px 0;
  color: var(--text-secondary);
}
</style>
