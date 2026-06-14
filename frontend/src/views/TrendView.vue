<template>
  <div class="page-container">
    <div class="page-header">
      <h2>趋势图表</h2>
      <p>纵向追踪指标变化，发现潜在趋势</p>
    </div>

    <el-card style="margin-bottom:20px;">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="12">
          <el-form-item label="指标（可多选）" label-position="top" style="margin-bottom:0;">
            <el-select
              v-model="selectedMetrics"
              filterable
              multiple
              collapse-tags
              collapse-tags-tooltip
              placeholder="搜索指标"
              style="width:100%"
              @change="onMetricsChange"
            >
              <el-option v-for="m in allMetrics" :key="m.metric_name" :label="`${m.metric_name} (${m.abnormal_count}次异常)`" :value="m.metric_name" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-form-item label="时间范围" label-position="top" style="margin-bottom:0;">
            <el-select v-model="rangeMonths" @change="onMetricsChange">
              <el-option label="近3个月" :value="3" />
              <el-option label="近半年" :value="6" />
              <el-option label="近1年" :value="12" />
              <el-option label="全部" :value="0" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-form-item label="分享" label-position="top" style="margin-bottom:0;">
            <el-button @click="handleShare">分享趋势</el-button>
          </el-form-item>
        </el-col>
      </el-row>
    </el-card>

    <template v-if="chartDataList.length > 0">
      <el-card v-for="(cd, idx) in chartDataList" :key="cd.metric_name" style="margin-bottom:20px;">
        <template #header>
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
            <span>{{ cd.metric_name }} 趋势</span>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
              <span style="font-size:12px;color:var(--text-secondary);">
                {{ cd.unit }}&nbsp;
                <span v-if="cd.ref_min != null || cd.ref_max != null">
                  ({{ cd.ref_min != null ? cd.ref_min : '' }}{{ cd.ref_min != null && cd.ref_max != null ? '~' : '' }}{{ cd.ref_max != null ? cd.ref_max : '' }})
                </span>
              </span>
              <el-tag
                :type="cd.direction === 'up' ? 'danger' : cd.direction === 'down' ? 'warning' : 'info'"
                effect="plain"
                size="small"
              >
                {{ cd.direction === 'up' ? '↑ 上升' : cd.direction === 'down' ? '↓ 下降' : '→ 稳定' }}
              </el-tag>
            </div>
          </div>
        </template>
        <div :ref="el => setChartRef(el, idx)" class="chart-container" style="height:380px;"></div>
        <el-table :data="cd.data_points" size="small" stripe style="margin-top:16px;">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column label="结果" min-width="120">
            <template #default="{ row }">
              <span :style="{ color: row.is_abnormal ? '#ef4444' : 'inherit', fontWeight: row.is_abnormal ? 'bold' : 'normal' }">
                {{ row.value }}
              </span>
              <span style="color:var(--text-secondary);margin-left:4px;">{{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="参考区间" width="160">
            <template #default="{ row }">
              {{ row.ref_min != null && row.ref_max != null ? `${row.ref_min} ~ ${row.ref_max}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="institution" label="机构" min-width="150" />
          <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />
        </el-table>
      </el-card>
    </template>

    <el-empty v-else description="请选择指标查看趋势">
      <el-button v-if="!authStore.currentPatient" type="primary" @click="router.push('/patients')">
        先去添加患者
      </el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { useAuthStore } from '../stores/auth'
import { getTrend, listMetricsWithAbnormalCount, generateShare } from '../api/index'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const allMetrics = ref<{metric_name: string, abnormal_count: number}[]>([])
const selectedMetrics = ref<string[]>([])
const rangeMonths = ref(0)
const chartDataList = ref<any[]>([])
const chartRefs = ref<(HTMLElement | null)[]>([])
const chartInstances: any[] = []

function setChartRef(el: any, idx: number) {
  chartRefs.value[idx] = el
}

async function loadAllMetrics() {
  if (!authStore.currentPatient) return
  try {
    const res = await listMetricsWithAbnormalCount(authStore.currentPatient.id)
    allMetrics.value = res.data || []
  } catch { /* ignore */ }
}

async function loadAllTrends() {
  if (!selectedMetrics.value.length || !authStore.currentPatient) {
    chartDataList.value = []
    return
  }
  try {
    const promises = selectedMetrics.value.map((m) =>
      getTrend(m, authStore.currentPatient!.id, rangeMonths.value > 0 ? rangeMonths.value : undefined),
    )
    const results = await Promise.all(promises)
    chartDataList.value = results.map((r) => r.data)
    await nextTick()
    disposeAllCharts()
    await nextTick()
    renderAllCharts()
  } catch {
    ElMessage.error('加载趋势失败')
  }
}

function onMetricsChange() {
  loadAllTrends()
}

function disposeAllCharts() {
  for (const inst of chartInstances) {
    inst?.dispose()
  }
  chartInstances.length = 0
}

function renderAllCharts() {
  for (let i = 0; i < chartDataList.value.length; i++) {
    const el = chartRefs.value[i]
    if (!el) continue
    const cd = chartDataList.value[i]
    if (!cd.data_points || cd.data_points.length === 0) continue
    const chart = echarts.init(el)
    chartInstances.push(chart)

    const dps = cd.data_points
    const dates = dps.map((d: any) => d.date)
    const values = dps.map((d: any) => d.value)

    const markAreas: any[] = []
    if (cd.ref_min != null && cd.ref_max != null) {
      markAreas.push([
        { yAxis: String(cd.ref_min), itemStyle: { color: 'rgba(16,185,129,0.08)' } },
        { yAxis: String(cd.ref_max), itemStyle: { color: 'rgba(16,185,129,0.08)' } },
      ])
    }

    const series: any[] = [
      {
        name: cd.metric_name,
        type: 'line',
        data: values.map((v: number, di: number) => ({
          value: v,
          itemStyle: { color: dps[di].is_abnormal ? '#ef4444' : '#6366f1', borderColor: dps[di].is_abnormal ? '#ef4444' : '#6366f1' },
          symbolSize: dps[di].is_abnormal ? 12 : 8,
        })),
        smooth: true,
        symbol: 'circle',
        lineStyle: { color: '#6366f1', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99,102,241,0.15)' },
            { offset: 1, color: 'rgba(99,102,241,0.02)' },
          ]),
        },
        markArea:
          markAreas.length > 0
            ? { silent: true, data: markAreas }
            : undefined,
      },
    ]

    if (cd.trend_line && cd.trend_line.length > 1) {
      series.push({
        name: '趋势线',
        type: 'line',
        data: cd.trend_line,
        smooth: false,
        symbol: 'none',
        lineStyle: { type: 'dashed', color: '#f59e0b', width: 2 },
      })
    }

    chart.setOption({
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          if (!params || params.length === 0) return ''
          const idx = params[0].dataIndex
          const d = dps[idx]
          return `<b>${d.date}</b><br/>结果: ${d.value} ${d.unit}<br/>参考: ${d.ref_min ?? '--'} ~ ${d.ref_max ?? '--'}<br/>${d.institution || ''}`
        },
      },
      legend: { show: series.length > 1, bottom: 0 },
      grid: { left: 50, right: 30, top: 50, bottom: 50 },
      xAxis: { type: 'category', data: dates, axisLabel: { rotate: 30, fontSize: 11 } },
      yAxis: { type: 'value', name: cd.unit, scale: true },
      series,
      dataZoom: [
        { type: 'slider', start: 0, end: 100, height: 20, bottom: 25 },
        { type: 'inside' },
      ],
    })
  }
}

async function handleShare() {
  if (!authStore.currentPatient) {
    ElMessage.warning('请先选择患者')
    return
  }
  try {
    const res = await generateShare({
      patient_id: authStore.currentPatient.id,
      metric_names: selectedMetrics.value.length > 0 ? selectedMetrics.value : undefined,
      expire_days: 7,
    })
    const base = import.meta.env.PROD
      ? (import.meta.env.VITE_API_BASE_URL || '').replace(':35001', ':35000')
      : window.location.origin
    const url = `${base}/share/${res.data.token}`
    const input = document.createElement('textarea')
    input.value = url
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    ElMessage.success('链接已复制到剪贴板')
    ElMessageBox.alert(
      `链接: ${url}<br/>有效期: ${res.data.expires_at}`,
      '分享链接',
      { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' },
    )
  } catch {
    ElMessage.error('生成分享链接失败')
  }
}

watch(
  () => authStore.currentPatient,
  (np) => {
    if (np && selectedMetrics.value.length > 0) loadAllTrends()
  },
)

onMounted(async () => {
  await loadAllMetrics()

  if (route.query.metric) {
    const m = route.query.metric as string
    if (allMetrics.value.some(x => x.metric_name === m)) {
      selectedMetrics.value = [m]
      loadAllTrends()
    }
  }
})

onUnmounted(() => {
  disposeAllCharts()
})

window.addEventListener('resize', () => {
  for (const inst of chartInstances) {
    inst?.resize()
  }
})
</script>
