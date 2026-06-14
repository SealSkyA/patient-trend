<template>
  <div class="page-container">
    <div class="page-header">
      <h2>报告库</h2>
      <p>查看、编辑、管理所有检查报告</p>
    </div>

    <el-card>
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
        <span style="font-weight:600;font-size:15px;">
          共 {{ reports.length }} 份报告
        </span>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            size="small"
            :clearable="true"
            style="width:240px;"
          />
          <el-input
            v-model="institutionFilter"
            placeholder="项目类别"
            size="small"
            clearable
            style="width:160px;"
            @keyup.enter="loadData"
          />
          <el-button type="primary" size="small" @click="loadData">搜索</el-button>
          <el-button size="small" @click="clearFilters">清除</el-button>
        </div>
        <el-button type="primary" size="small" @click="router.push('/entry')">
          <el-icon style="margin-right:4px;"><Plus /></el-icon> 录入新报告
        </el-button>
      </div>

      <el-table :data="reports" size="default" stripe highlight-current-row style="width:100%;">
        <el-table-column prop="exam_date" label="检查日期" width="130" sortable />
        <el-table-column prop="institution" label="项目类别" min-width="180" />
        <el-table-column label="指标数" width="90" align="center">
          <template #default="{ row }">{{ row.metric_count }}</template>
        </el-table-column>
        <el-table-column label="异常" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.abnormal_count > 0" type="danger" size="small" round>
              {{ row.abnormal_count }}
            </el-tag>
            <span v-else style="color:var(--success);font-weight:500;">0</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <div style="display:flex;flex-direction:column;gap:4px;">
              <el-button size="small" type="primary" link @click="viewDetail(row.id)">详情</el-button>
              <div style="display:flex;gap:8px;justify-content:center;">
                <el-button size="small" link @click="router.push('/trend')">趋势</el-button>
                <el-popconfirm title="确定删除？" @confirm="doDelete(row.id)">
                  <template #reference>
                    <el-button size="small" type="danger" link>删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="reports.length === 0 && loaded" class="empty-state">
        <div class="icon">📄</div>
        <p>暂无报告数据</p>
        <el-button type="primary" @click="router.push('/entry')" style="margin-top:12px;">
          录入第一份报告
        </el-button>
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="报告详情" width="900px" :close-on-click-modal="false">
      <template v-if="detail.id">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="检查日期">{{ detail.exam_date }}</el-descriptions-item>
            <el-descriptions-item label="项目类别">{{ detail.institution }}</el-descriptions-item>
            <el-descriptions-item label="备注">{{ detail.notes || '-' }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-left:16px;">
            <el-button size="small" type="primary" @click="editReport">编辑</el-button>
          </div>
        </div>

        <div v-if="detail.results?.some((r:any)=>r.is_abnormal)" style="margin-top:16px;">
          <div style="font-weight:600;font-size:14px;margin-bottom:8px;color:#ef4444;">异常指标</div>
          <el-table :data="detail.results.filter((r:any)=>r.is_abnormal)" size="small" border stripe>
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

        <el-table v-if="detail.results?.length" :data="detail.results" size="small" border style="margin-top:16px;">
          <el-table-column prop="metric_name" label="指标" min-width="130">
            <template #default="{ row }">
              <span v-if="!editMode">{{ row.metric_name }}</span>
              <el-input v-else v-model="row.metric_name" size="small" placeholder="指标名称" />
            </template>
          </el-table-column>
          <el-table-column label="结果" width="120">
            <template #default="{ row }">
              <span v-if="!editMode" :style="{ color: row.is_abnormal ? '#ef4444' : 'inherit', fontWeight: row.is_abnormal ? 'bold' : 'normal' }">
                {{ row.value }}
                <span style="color:var(--text-secondary);font-size:12px;"> {{ row.unit }}</span>
              </span>
              <el-input v-else v-model="row.value" type="number" size="small" placeholder="结果" />
            </template>
          </el-table-column>
          <el-table-column label="参考区间" width="150">
            <template #default="{ row }">
              <template v-if="!editMode">
                {{ row.ref_min != null ? `${row.ref_min} ~ ${row.ref_max}` : '-' }}
              </template>
              <div v-else style="display:flex;gap:4px;">
                <el-input v-model="row.ref_min" type="number" size="small" placeholder="最小" style="width:70px;" />
                <span style="align-self:center;">~</span>
                <el-input v-model="row.ref_max" type="number" size="small" placeholder="最大" style="width:70px;" />
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="!editMode">{{ row.notes || '-' }}</span>
              <el-input v-else v-model="row.notes" size="small" placeholder="备注" />
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_abnormal ? 'danger' : 'success'" size="small" round>
                {{ row.is_abnormal ? '异常' : '正常' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="editMode" label="操作" width="70" align="center">
            <template #default="{ $index }">
              <el-button size="small" type="danger" link @click="deleteResult($index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="editMode" style="margin-top:12px;">
          <el-button type="primary" size="small" @click="addResultRow">
            <el-icon style="margin-right:4px;"><Plus /></el-icon> 添加指标
          </el-button>
        </div>
      </template>
      <template #footer>
        <div v-if="editMode">
          <el-button @click="cancelEdit">取消</el-button>
          <el-button type="primary" @click="saveReport" :loading="false">保存</el-button>
        </div>
        <el-button v-else type="primary" @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { listReports, getReport, deleteReport, updateReport } from '../api/index'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const reports = ref<any[]>([])
const loaded = ref(false)
const detailVisible = ref(false)
const detail = ref<any>({ results: [] })
const dateRange = ref<[string, string] | null>(null)
const institutionFilter = ref('')
const editMode = ref(false)

async function loadData() {
  if (!authStore.currentPatient) {
    reports.value = []
    loaded.value = false
    return
  }
  try {
    const extra: Record<string, any> = {}
    if (dateRange.value && dateRange.value.length === 2) {
      extra.exam_date_start = dateRange.value[0]
      extra.exam_date_end = dateRange.value[1]
    }
    if (institutionFilter.value) {
      extra.institution = institutionFilter.value
    }
    const res = await listReports(authStore.currentPatient.id, 1, 200, extra)
    reports.value = res.data
    loaded.value = true
  } catch {
    ElMessage.error('加载失败')
  }
}

function clearFilters() {
  dateRange.value = null
  institutionFilter.value = ''
  loadData()
}

async function viewDetail(id: number) {
  try {
    const res = await getReport(id)
    detail.value = res.data
    detailVisible.value = true
  } catch {
    ElMessage.error('加载报告失败')
  }
}

async function doDelete(id: number) {
  try {
    await deleteReport(id)
    ElMessage.success('删除成功')
    await loadData()
  } catch {
    ElMessage.error('删除失败')
  }
}

function editReport() {
  editMode.value = true
}

async function saveReport() {
  try {
    const payload = {
      institution: detail.value.institution,
      exam_date: detail.value.exam_date,
      notes: detail.value.notes,
      results: detail.value.results.map((r: any) => ({
        metric_name: r.metric_name,
        value: parseFloat(r.value) || 0,
        unit: r.unit || '',
        ref_min: r.ref_min != null ? parseFloat(r.ref_min) : null,
        ref_max: r.ref_max != null ? parseFloat(r.ref_max) : null,
        notes: r.notes || '',
      })),
    }
    await updateReport(detail.value.id, payload)
    ElMessage.success('保存成功')
    editMode.value = false
    await loadData()
  } catch {
    ElMessage.error('保存失败')
  }
}

function cancelEdit() {
  editMode.value = false
}

function deleteResult(idx: number) {
  detail.value.results.splice(idx, 1)
}

function addResultRow() {
  detail.value.results.push({ metric_name: '', value: '', unit: '', ref_min: null, ref_max: null, notes: '' })
}

watch(() => authStore.currentPatient, (np) => {
  if (np) loadData()
}, { immediate: true })

const route$ = useRoute()
watch(() => route$.query.id, (id) => {
  if (id) viewDetail(Number(id))
}, { immediate: true })
</script>

<style scoped>
.el-table .action-column .el-button {
  min-width: 60px;
}
</style>

<style scoped>
.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: nowrap;
}

.action-buttons .el-button {
  white-space: nowrap;
  padding: 4px 8px;
}
</style>
