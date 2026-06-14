<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ dashboard.patient_name || '请选择患者' }} - 健康概览</h2>
    </div>

    <el-card v-if="dashboard.medication_compare" style="margin-bottom:20px;">
      <template #header>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
          <span style="font-weight:600;">
            最新用药
            <el-tag size="small" type="primary" style="margin-left:8px;">{{ dashboard.medication_compare.doctor }}</el-tag>
            <span style="font-size:12px;color:var(--text-secondary);margin-left:4px;">{{ dashboard.medication_compare.created_at?.slice(0, 10) }}</span>
          </span>
          <el-button v-if="hasChanges" size="small" type="primary" link @click="showPrevDetail = true">
            查看上次用药详情
          </el-button>
        </div>
      </template>
        <el-table :data="dashboard.medication_compare.drugs" size="small" stripe border fit>
          <el-table-column prop="drug_name" label="药物名称" min-width="120" />
          <el-table-column prop="specification" label="规格" width="80" />
          <el-table-column prop="dosage" label="用量" width="70" />
          <el-table-column prop="usage_method" label="使用方法" min-width="100" />
          <el-table-column prop="notes" label="备注" min-width="100" show-overflow-tooltip />
          <el-table-column label="状态" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'new' ? 'success' : row.status === 'changed' ? 'warning' : row.status === 'removed' ? 'danger' : 'info'" size="small">
                {{ row.status === 'new' ? '新增' : row.status === 'changed' ? '变更' : row.status === 'removed' ? '停用' : '不变' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
    </el-card>

    <!-- 弹窗：上次用药详情 -->
    <el-dialog v-model="showPrevDetail" title="上次用药详情" width="800px">
      <template v-if="prevDetail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="开药医生">{{ prevDetail.doctor }}</el-descriptions-item>
          <el-descriptions-item label="记录时间">{{ prevDetail.created_at?.slice(0, 16) }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="prevDetail.drugs" size="small" border stripe fit>
          <el-table-column prop="drug_name" label="药物名称" min-width="120" />
          <el-table-column prop="specification" label="规格" width="80" />
          <el-table-column prop="dosage" label="用量" width="70" />
          <el-table-column prop="usage_method" label="使用方法" min-width="100" />
          <el-table-column prop="notes" label="备注" min-width="100" show-overflow-tooltip />
        </el-table>
      </template>
      <div v-else style="text-align:center;padding:30px;color:var(--text-secondary);">上次无用药记录</div>
    </el-dialog>

    <div class="card-grid">
      <div class="stat-card clickable" @click="openYearlyReports">
        <div class="label">报告总数</div>
        <div class="value">{{ totalReports }}</div>
      </div>
      <div class="stat-card clickable" @click="showAnomalyModal = true">
        <div class="label">异常指标</div>
        <div class="value" :class="totalAnomalies > 0 ? 'danger' : 'success'">{{ totalAnomalies }}</div>
      </div>
      <div class="stat-card clickable" @click="showWatchModal = true">
        <div class="label">需关注趋势</div>
        <div class="value" :class="dashboard.watch_list.length > 0 ? 'warning' : 'success'">{{ dashboard.watch_list.length }}</div>
      </div>
      <div class="stat-card clickable" @click="openLatestReport">
        <div class="label">最新检查</div>
        <div class="value" style="font-size:18px;">{{ dashboard.latest_report?.exam_date || '-' }}</div>
      </div>
    </div>

    <div v-if="!authStore.currentPatient" class="empty-state">
      <div class="icon">&#x1f464;</div>
      <p>请先在顶部选择患者，或前往「患者管理」添加</p>
      <el-button type="primary" @click="router.push('/patients')" style="margin-top:12px;">管理患者</el-button>
    </div>

    <template v-else>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
        <el-card class="clickable-card" @click="showAnomalyModal = true">
          <template #header>
            <span style="display:flex;align-items:center;gap:6px;">
              <el-icon color="#ef4444"><WarningFilled /></el-icon> 异常指标
              <span style="margin-left:auto;font-size:12px;color:var(--text-secondary);">点击查看详情</span>
            </span>
          </template>
          <div ref="anomalyChartRef" class="chart-container" style="height:280px;"></div>
          <div v-if="dashboard.anomalies.length === 0" style="text-align:center;color:var(--text-secondary);padding:30px;">
            暂无异常指标
          </div>
        </el-card>

        <el-card class="clickable-card" @click="showWatchModal = true">
          <template #header>
            <span style="display:flex;align-items:center;gap:6px;">
              <el-icon color="#f59e0b"><TrendCharts /></el-icon> 需关注趋势
              <span style="margin-left:auto;font-size:12px;color:var(--text-secondary);">点击查看详情</span>
            </span>
          </template>
          <div v-if="dashboard.watch_list.length > 0" style="max-height:280px;overflow-y:auto;">
            <div
              v-for="w in dashboard.watch_list"
              :key="w.metric_name"
              class="watch-row"
              @click.stop="openTrendModal(w.metric_name)"
            >
              <div>
                <div style="font-weight:600;">{{ w.metric_name }}</div>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">{{ w.warning }}</div>
              </div>
              <el-tag
                :type="w.direction === 'up' ? 'danger' : 'warning'"
                size="small"
                effect="plain"
              >
                {{ w.direction === 'up' ? '上升' : '下降' }}
              </el-tag>
            </div>
          </div>
          <div v-else style="text-align:center;color:var(--text-secondary);padding:30px;">
            暂无异常趋势
          </div>
        </el-card>
      </div>

      <el-card style="margin-bottom:24px;" class="clickable-card" @click="showReportModal = true">
        <template #header>
          <span style="display:flex;align-items:center;gap:6px;">
            <el-icon color="#6366f1"><Histogram /></el-icon> 各报告异常情况
          </span>
        </template>
        <div ref="reportChartRef" class="chart-container" style="height:300px;"></div>
      </el-card>

      <el-card class="clickable-card">
        <template #header>
          <span>最近报告列表（点击查看详情）</span>
        </template>
        <el-table :data="dashboard.recent_reports" size="default" style="width:100%;cursor:pointer;" @row-click="openReportDetail">
          <el-table-column prop="exam_date" label="检查日期" width="140" />
          <el-table-column prop="institution" label="项目类别" min-width="180" />
          <el-table-column prop="metric_count" label="指标数" width="90" align="center" />
          <el-table-column label="异常数" width="90" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.abnormal_count > 0" type="danger" size="small" round>{{ row.abnormal_count }}</el-tag>
              <span v-else style="color:var(--success);">0</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click.stop="openReportDetail(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <!-- 弹窗：最新检查详情 -->
    <el-dialog v-model="showLatestReport" :title="'最新检查 - ' + latestReportDetail.exam_date" width="700px">
      <template v-if="latestReportDetail.id">
        <div style="font-size:14px;color:var(--text-secondary);margin-bottom:12px;">
          项目类别：{{ latestReportDetail.institution }}
          <span v-if="latestReportDetail.notes" style="margin-left:16px;">备注：{{ latestReportDetail.notes }}</span>
        </div>
        <div v-if="latestReportDetail.results?.length" style="font-size:15px;line-height:2.2;">
          <div
            v-for="r in latestReportDetail.results"
            :key="r.metric_name"
            class="report-line"
            :style="r.is_abnormal ? 'color:#ef4444;font-weight:600;background:#fef2f2;padding:8px 12px;border-radius:8px;margin-bottom:4px;' : 'padding:8px 12px;'"
          >
            {{ r.metric_name }}：<b>{{ r.value }}</b> {{ r.unit }}
            <span v-if="r.ref_min != null || r.ref_max != null" style="font-size:13px;color:var(--text-secondary);margin-left:12px;">
              （参考：{{ r.ref_min != null ? r.ref_min : '' }}{{ r.ref_min != null && r.ref_max != null ? '~' : '' }}{{ r.ref_max != null ? r.ref_max : '' }}）
            </span>
            <el-tag v-if="r.is_abnormal" type="danger" size="small" style="margin-left:8px;">异常</el-tag>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗：本年度报告列表 -->
    <el-dialog v-model="showYearlyModal" title="本年度报告" width="800px">
      <div v-if="yearlyReports.length === 0" style="text-align:center;padding:30px;color:var(--text-secondary);">暂无报告</div>
      <el-table v-else :data="yearlyReports" size="small" border @row-click="openReportDetail" style="cursor:pointer;">
        <el-table-column prop="exam_date" label="检查日期" width="130" />
        <el-table-column prop="institution" label="项目类别" min-width="200" />
        <el-table-column prop="metric_count" label="指标数" width="80" align="center" />
        <el-table-column label="异常" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.abnormal_count > 0" type="danger" size="small" round>{{ row.abnormal_count }}</el-tag>
            <span v-else style="color:var(--success);">0</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click.stop="openReportDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 弹窗：异常指标详情 -->
    <el-dialog v-model="showAnomalyModal" title="近期异常指标" width="900px">
      <div v-if="dashboard.anomalies.length === 0" style="text-align:center;padding:30px;color:var(--text-secondary);">暂无异常</div>
      <el-table v-else :data="dashboard.anomalies" size="small" border stripe>
        <el-table-column prop="exam_date" label="检查日期" width="120" sortable />
        <el-table-column prop="institution" label="项目类别" min-width="180" />
        <el-table-column prop="metric_name" label="指标" min-width="140" />
        <el-table-column label="结果" width="130">
          <template #default="{ row }">
            <span style="color:#ef4444;font-weight:bold;">{{ row.value }}</span>
            <span style="color:var(--text-secondary);font-size:12px;"> {{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="参考区间" width="170">
          <template #default="{ row }">
            {{ row.ref_min != null && row.ref_max != null ? `${row.ref_min} ~ ${row.ref_max}` : row.ref_min != null ? `> ${row.ref_min}` : row.ref_max != null ? `< ${row.ref_max}` : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 弹窗：关注趋势详情 -->
    <el-dialog v-model="showWatchModal" title="关注趋势" width="700px">
      <div v-if="dashboard.watch_list.length === 0" style="text-align:center;padding:30px;color:var(--text-secondary);">暂无</div>
      <div v-else v-for="w in dashboard.watch_list" :key="w.metric_name" style="margin-bottom:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <span style="font-weight:600;">{{ w.metric_name }}</span>
          <el-button size="small" @click="openTrendModal(w.metric_name)">查看趋势图</el-button>
        </div>
        <div style="display:flex;gap:12px;">
          <span v-for="(v, i) in w.recent_values" :key="i" class="watch-val">
            {{ w.recent_dates[i] }}: <b>{{ v }}</b>
          </span>
        </div>
        <el-tag :type="w.direction === 'up' ? 'danger' : 'warning'" size="small" style="margin-top:4px;">{{ w.warning }}</el-tag>
      </div>
    </el-dialog>

    <!-- 弹窗：报告列表 -->
    <el-dialog v-model="showReportModal" title="最近报告" width="800px">
      <el-table :data="dashboard.recent_reports" size="small" border @row-click="openReportDetail" style="cursor:pointer;">
        <el-table-column prop="exam_date" label="日期" width="120" />
        <el-table-column prop="institution" label="机构" min-width="180" />
        <el-table-column prop="metric_count" label="指标数" width="80" align="center" />
        <el-table-column label="异常数" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.abnormal_count > 0" type="danger" size="small" round>{{ row.abnormal_count }}</el-tag>
            <span v-else>0</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click.stop="openReportDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 弹窗：单个报告详情 -->
    <el-dialog v-model="showReportDetail" :title="'报告详情 - ' + reportDetail.exam_date" width="750px">
      <template v-if="reportDetail.id">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="检查日期">{{ reportDetail.exam_date }}</el-descriptions-item>
          <el-descriptions-item label="项目类别">{{ reportDetail.institution }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ reportDetail.notes || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="reportDetail.results?.some((r:any)=>r.is_abnormal)" style="margin-top:16px;">
          <div style="font-weight:600;font-size:14px;margin-bottom:8px;color:#ef4444;">异常指标</div>
          <el-table :data="reportDetail.results.filter((r:any)=>r.is_abnormal)" size="small" border stripe>
            <el-table-column prop="metric_name" label="指标" min-width="150" />
            <el-table-column label="结果" width="120">
              <template #default="{ row }">
                <span style="color:#ef4444;font-weight:bold;">{{ row.value }}</span>
                <span style="color:var(--text-secondary);font-size:12px;"> {{ row.unit }}</span>
              </template>
            </el-table-column>
            <el-table-column label="参考区间" width="150">
              <template #default="{ row }">
                {{ row.ref_min != null ? `${row.ref_min} ~ ${row.ref_max}` : '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-table v-if="reportDetail.results?.length" :data="reportDetail.results" size="small" border style="margin-top:16px;">
          <el-table-column prop="metric_name" label="指标" min-width="130" />
          <el-table-column label="结果" width="120">
            <template #default="{ row }">
              <span :style="{ color: row.is_abnormal ? '#ef4444' : 'inherit', fontWeight: row.is_abnormal ? 'bold' : 'normal' }">
                {{ row.value }}
              </span>
              <span style="color:var(--text-secondary);font-size:12px;"> {{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="参考区间" width="150">
            <template #default="{ row }">
              {{ row.ref_min != null ? `${row.ref_min} ~ ${row.ref_max}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_abnormal ? 'danger' : 'success'" size="small" round>
                {{ row.is_abnormal ? '异常' : '正常' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>

    <!-- 弹窗：趋势小图 -->
    <el-dialog v-model="showTrendModal" :title="trendMetric + ' 趋势'" width="800px">
      <div ref="trendChartRef" style="width:100%;height:400px;"></div>
      <el-table v-if="trendData.length > 0" :data="trendData" size="small" border style="margin-top:16px;">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column label="结果" min-width="120">
          <template #default="{ row }">
            <span :style="{ color: row.is_abnormal ? '#ef4444' : 'inherit', fontWeight: row.is_abnormal ? 'bold' : 'normal' }">
              {{ row.value }}
            </span>
            <span style="color:var(--text-secondary);margin-left:4px;">{{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="参考区间" width="150">
          <template #default="{ row }">
            {{ row.ref_min != null ? `${row.ref_min} ~ ${row.ref_max}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="institution" label="机构" min-width="150" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getDashboard, getReport, getTrend, listReports } from '../api/index'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { WarningFilled, TrendCharts, Histogram } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const router = useRouter()
const dashboard = ref<any>({ anomalies: [], watch_list: [], recent_reports: [], latest_report: null, patient_name: '' })

const totalReports = computed(() => dashboard.value.recent_reports?.length || 0)
const totalAnomalies = computed(() => dashboard.value.anomalies?.length || 0)

// 弹窗状态
const showAnomalyModal = ref(false)
const showWatchModal = ref(false)
const showReportModal = ref(false)
const showYearlyModal = ref(false)
const showReportDetail = ref(false)
const showTrendModal = ref(false)
const showPrevDetail = ref(false)
const reportDetail = ref<any>({})
const yearlyReports = ref<any[]>([])
const trendMetric = ref('')
const trendData = ref<any[]>([])
const latestReportDetail = ref<any>({})
const showLatestReport = ref(false)
const prevDetail = ref<any>(null)
const hasChanges = computed(() => dashboard.value.medication_compare?.drugs?.some((d: any) => d.status !== 'unchanged'))

// 图表引用
const anomalyChartRef = ref<HTMLElement | null>(null)
const reportChartRef = ref<HTMLElement | null>(null)
const trendChartRef = ref<HTMLElement | null>(null)
let anomalyChart: any = null
let reportChart: any = null

async function renderAnomalyChart() {
  if (!anomalyChart) anomalyChart = echarts.init(anomalyChartRef.value)
  const anomalies = dashboard.value.anomalies || []
  if (anomalies.length === 0) { anomalyChart.clear(); return }

  const metrics = [...new Set(anomalies.map((a: any) => a.metric_name))]
  const data = metrics.map((m: any) => ({
    name: m,
    value: anomalies.filter((a: any) => a.metric_name === m).length,
  }))
  const isMobile = window.innerWidth < 768

  anomalyChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 项异常' },
    series: [{
      type: 'pie', radius: isMobile ? ['35%', '65%'] : ['45%', '75%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { fontSize: isMobile ? 10 : 12, color: '#64748b' },
      data,
    }],
  })
}

function renderReportChart() {
  if (!reportChartRef.value) return
  if (!reportChart) reportChart = echarts.init(reportChartRef.value)
  const reports = dashboard.value.recent_reports || []
  if (reports.length === 0) { reportChart.clear(); return }
  const isMobile = window.innerWidth < 768

  reportChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { bottom: isMobile ? -5 : 0, textStyle: { color: '#64748b', fontSize: isMobile ? 11 : 12 } },
    grid: { left: isMobile ? 30 : 40, right: isMobile ? 10 : 20, top: 20, bottom: isMobile ? 50 : 40 },
    xAxis: { type: 'category', data: reports.map((r: any) => r.exam_date).reverse(), axisLabel: { rotate: isMobile ? 45 : 30, fontSize: isMobile ? 10 : 11 } },
    yAxis: { type: 'value' },
    series: [
      { name: '总指标', type: 'bar', data: reports.map((r: any) => r.metric_count).reverse(), itemStyle: { color: '#6366f1', borderRadius: [4, 4, 0, 0] }, barWidth: isMobile ? 12 : 18 },
      { name: '异常数', type: 'bar', data: reports.map((r: any) => r.abnormal_count).reverse(), itemStyle: { color: '#ef4444', borderRadius: [4, 4, 0, 0] }, barWidth: isMobile ? 12 : 18 },
    ],
  })
}

async function openYearlyReports() {
  if (!authStore.currentPatient) return
  showYearlyModal.value = true
  try {
    const year = new Date().getFullYear().toString()
    const res = await listReports(authStore.currentPatient.id, 1, 100)
    yearlyReports.value = (res.data || []).filter((r: any) => r.exam_date?.startsWith(year))
  } catch {
    ElMessage.error('加载报告失败')
  }
}

async function openLatestReport() {
  if (!dashboard.value.latest_report?.id) {
    ElMessage.info('暂无报告')
    return
  }
  try {
    const res = await getReport(dashboard.value.latest_report.id)
    const data = res.data
    if (data.results) {
      data.results = [...data.results].sort((a: any, b: any) => (b.is_abnormal ? 1 : 0) - (a.is_abnormal ? 1 : 0))
    }
    latestReportDetail.value = data
    showLatestReport.value = true
  } catch {
    ElMessage.error('加载报告失败')
  }
}

async function openReportDetail(row: any) {
  try {
    const res = await getReport(row.id)
    reportDetail.value = res.data
    showReportDetail.value = true
  } catch {
    ElMessage.error('加载报告失败')
  }
}

async function openTrendModal(metric: string) {
  trendMetric.value = metric
  showTrendModal.value = true
  if (!authStore.currentPatient) return
  try {
    const res = await getTrend(metric, authStore.currentPatient.id)
    trendData.value = res.data.data_points || []
    await nextTick()
    renderTrendChart()
  } catch {
    ElMessage.error('加载趋势失败')
  }
}

function renderTrendChart() {
  if (!trendChartRef.value || trendData.value.length === 0) return
  const chart = echarts.init(trendChartRef.value)
  const dates = trendData.value.map((d: any) => d.date)
  const values = trendData.value.map((d: any) => d.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: 'value', scale: true },
    series: [{
      type: 'line', data: values, smooth: true, symbol: 'circle', symbolSize: 8,
      lineStyle: { color: '#6366f1', width: 2 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(99,102,241,0.15)' }, { offset: 1, color: 'rgba(99,102,241,0.02)' }]) },
      markArea: trendData.value.length > 0 && trendData.value[0]?.ref_min != null && trendData.value[0]?.ref_max != null ? {
        silent: true,
        data: [[{ yAxis: String(trendData.value[0].ref_min), itemStyle: { color: 'rgba(16,185,129,0.1)' } }, { yAxis: String(trendData.value[0].ref_max), itemStyle: { color: 'rgba(16,185,129,0.1)' } }]],
      } : undefined,
    }],
  })
}

async function loadData() {
  if (!authStore.currentPatient) return
  try {
    const res = await getDashboard(authStore.currentPatient.id)
    dashboard.value = res.data
    const mc = dashboard.value.medication_compare
    if (mc && mc.drugs?.some((d: any) => d.status !== 'new')) {
      prevDetail.value = {
        doctor: mc.doctor,
        created_at: mc.created_at,
        drugs: mc.drugs.filter((d: any) => d.status !== 'new').map((d: any) => ({
          drug_name: d.drug_name,
          specification: d.prev_specification || '-',
          dosage: d.prev_dosage || '-',
          usage_method: d.usage_method || '-',
        }))
      }
    } else {
      prevDetail.value = null
    }
    await nextTick()
    renderAnomalyChart()
    renderReportChart()
  } catch {
    ElMessage.error('加载仪表板失败')
  }
}

const unwatch = watch(() => authStore.currentPatient, (np) => {
  if (np) loadData()
}, { immediate: true })

onMounted(() => {
  window.addEventListener('resize', () => {
    anomalyChart?.resize()
    reportChart?.resize()
    loadData()
  })
})

onUnmounted(() => {
  unwatch()
  anomalyChart?.dispose()
  reportChart?.dispose()
})
</script>

<style scoped>
.clickable {
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.clickable:hover {
  transform: translateY(-2px);
}
.clickable-card {
  cursor: pointer;
}
.watch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}
.watch-row:hover {
  background: #f8fafc;
}
.watch-val {
  font-size: 13px;
  color: var(--text-secondary);
}

.report-line {
  padding: 8px 0;
  border-bottom: 1px dashed var(--border);
  line-height: 1.6;
}

@media (max-width: 768px) {
  .card-grid {
    grid-template-columns: 1fr 1fr !important;
    gap: 10px;
  }
  .stat-card {
    padding: 16px;
  }
  .stat-card .value {
    font-size: 24px !important;
  }
  .stat-card .label {
    font-size: 12px;
  }
  .page-container > div[style*="grid-template-columns"] {
    grid-template-columns: 1fr !important;
  }
  .chart-container {
    height: 240px !important;
  }
}
</style>
