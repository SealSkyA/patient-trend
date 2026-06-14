<template>
  <div v-if="loaded" class="page-container">
    <el-card v-if="error" style="max-width:500px;margin:40px auto;">
      <el-result icon="error" :title="error" sub-title="分享链接可能已过期或不存在" />
    </el-card>

    <template v-else>
      <div class="page-header">
        <h2>健康趋势分享</h2>
        <p>{{ data.patient_info?.name }} 的检查报告趋势</p>
      </div>

      <el-descriptions :column="2" border size="small" style="margin-bottom:24px;">
        <el-descriptions-item label="姓名">{{ data.patient_info?.name }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ data.patient_info?.gender || '-' }}</el-descriptions-item>
        <el-descriptions-item label="出生日期">{{ data.patient_info?.birth_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="有效期至">
          <el-tag type="warning" size="small" effect="plain">{{ formatDate(data.expires_at) }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div v-for="t in data.trends" :key="t.metric_name" style="margin-bottom:24px;">
        <el-card>
          <template #header>
            <span>{{ t.metric_name }}
              <span style="color:var(--text-secondary);font-size:13px;font-weight:400;">
                ({{ t.unit }}{{ t.ref_min != null ? ` | 参考: ${t.ref_min}~${t.ref_max}` : '' }})
              </span>
            </span>
          </template>
          <div :ref="(el: any) => { if (el) chartRefs[t.metric_name] = el }" style="width:100%;height:320px;"></div>
        </el-card>
      </div>
    </template>
  </div>
  <div v-else style="display:flex;justify-content:center;align-items:center;height:100vh;">
    <el-icon class="is-loading" :size="32"><Loading /></el-icon>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import api from '../api/client'
import { Loading } from '@element-plus/icons-vue'

const route = useRoute()
const loaded = ref(false)
const error = ref('')
const data = reactive<any>({ trends: [], patient_info: {} })
const chartRefs: Record<string, HTMLElement> = {}

function formatDate(d: string) {
  if (!d) return '-'
  return d.split('T')[0]
}

onMounted(async () => {
  try {
    const res = await api.get(`/share/${route.params.token}`)
    Object.assign(data, res.data)
    loaded.value = true
    await nextTick()
    renderCharts()
  } catch (e: any) {
    if (e.response?.status === 410) error.value = '分享链接已过期'
    else if (e.response?.status === 404) error.value = '分享链接不存在'
    else error.value = '加载失败，请重试'
    loaded.value = true
  }
})

function renderCharts() {
  for (const t of data.trends) {
    const el = chartRefs[t.metric_name]
    if (!el || t.data_points.length === 0) continue
    const chart = echarts.init(el)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 20, top: 20, bottom: 40 },
      xAxis: {
        type: 'category',
        data: t.data_points.map((d: any) => d.date),
        axisLabel: { rotate: 30, fontSize: 11 },
      },
      yAxis: { type: 'value', name: t.unit, scale: true },
      series: [{
        type: 'line',
        data: t.data_points.map((d: any) => d.value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#6366f1', width: 2 },
        areaStyle: { color: 'rgba(99,102,241,0.1)' },
        markArea: t.ref_min != null && t.ref_max != null ? {
          silent: true,
          data: [[
            { yAxis: String(t.ref_min), itemStyle: { color: 'rgba(16,185,129,0.1)' } },
            { yAxis: String(t.ref_max), itemStyle: { color: 'rgba(16,185,129,0.1)' } },
          ]],
        } : undefined,
      }],
    })
  }
}
</script>
