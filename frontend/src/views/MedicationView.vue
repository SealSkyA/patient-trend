<template>
  <div class="page-container">
    <div class="page-header">
      <h2>用药记录</h2>
      <p>追踪患者用药历史，发现处方变化</p>
    </div>

    <el-card>
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
        <span style="font-weight:600;font-size:15px;">共 {{ records.length }} 条记录</span>
        <el-button type="primary" size="small" @click="openCreate">
          <el-icon style="margin-right:4px;"><Plus /></el-icon> 新增用药
        </el-button>
      </div>

      <el-table :data="records" size="default" stripe highlight-current-row>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column prop="doctor" label="开药医生" min-width="120" />
        <el-table-column prop="start_date" label="开始日期" width="120" />
        <el-table-column prop="item_count" label="药品数" width="80" align="center" />
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <div style="display:flex;flex-direction:column;gap:4px;">
              <el-button size="small" type="primary" link @click="viewDetail(row.id)">详情</el-button>
              <el-popconfirm title="确定删除？" @confirm="doDelete(row.id)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="records.length === 0 && loaded" class="empty-state">
        <div class="icon">&#x1f48a;</div>
        <p>暂无用药记录</p>
        <el-button type="primary" @click="openCreate" style="margin-top:12px;">添加第一条用药记录</el-button>
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="formVisible" :title="editingId ? '编辑用药' : '新增用药'" width="700px" :close-on-click-modal="false">
      <el-form label-width="90px" label-position="right">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12">
            <el-form-item label="开药医生" required>
              <el-input v-model="form.doctor" placeholder="医生姓名" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="开始日期">
              <el-date-picker v-model="form.start_date" type="date" placeholder="选填" style="width:100%;" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="用药备注" />
        </el-form-item>
      </el-form>

      <div style="margin-top:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <span style="font-weight:600;">药品清单</span>
          <el-button size="small" type="primary" text @click="addDrug">+ 添加药品</el-button>
        </div>
        <div v-for="(drug, idx) in form.items" :key="idx" style="background:#f8fafc;border-radius:8px;padding:12px;margin-bottom:8px;">
          <el-row :gutter="8" align="middle">
            <el-col :xs="12" :sm="6">
              <el-input v-model="drug.drug_name" placeholder="药物名称" size="small" />
            </el-col>
            <el-col :xs="12" :sm="5">
              <el-input v-model="drug.specification" placeholder="规格" size="small" />
            </el-col>
            <el-col :xs="12" :sm="4">
              <el-input v-model="drug.dosage" placeholder="用量" size="small" />
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-input v-model="drug.usage_method" placeholder="用法(饭前/饭后等)" size="small" />
            </el-col>
            <el-col :xs="24" :sm="3" style="display:flex;align-items:center;justify-content:flex-end;">
              <el-button size="small" type="danger" text @click="removeDrug(idx)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-col>
          </el-row>
          <el-input v-model="drug.notes" placeholder="药品备注" size="small" style="margin-top:6px;" />
        </div>
      </div>

      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="doSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="用药详情" width="700px">
      <template v-if="detail.id">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="开药医生">{{ detail.doctor }}</el-descriptions-item>
          <el-descriptions-item label="开始日期">{{ detail.start_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.notes || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-table v-if="detail.items?.length" :data="detail.items" size="small" border stripe style="margin-top:16px;">
          <el-table-column prop="drug_name" label="药物名称" min-width="120" />
          <el-table-column prop="specification" label="规格" width="100" />
          <el-table-column prop="dosage" label="用量" width="80" />
          <el-table-column prop="usage_method" label="使用方法" min-width="140" />
          <el-table-column prop="notes" label="备注" min-width="100" show-overflow-tooltip />
        </el-table>
      </template>
    </el-dialog>

    <!-- 对比弹窗 -->
    <el-dialog v-model="compareVisible" :title="'用药对比 - ' + compareRecord?.doctor" width="800px" :close-on-click-modal="false">
      <template v-if="compareItems.length > 0">
        <div style="margin-bottom:12px;font-size:13px;color:var(--text-secondary);">
          与上一次记录
          <span v-if="comparePrev" style="font-weight:600;color:var(--text);">
            ({{ comparePrev.doctor }} {{ comparePrev.created_at?.slice(0, 10) }})
          </span>
          对比
        </div>
        <el-tag
          v-for="item in compareItems"
          :key="item.drug_name"
          :type="item.status === 'new' ? 'success' : item.status === 'changed' ? 'warning' : item.status === 'removed' ? 'danger' : 'info'"
          size="small"
          style="margin:2px;"
        >
          {{ item.status === 'new' ? '新增' : item.status === 'changed' ? '变更' : item.status === 'removed' ? '停用' : '不变' }}：
          {{ item.drug_name }}
        </el-tag>

        <el-table :data="displayCompareItems" size="small" border stripe style="margin-top:12px;">
          <el-table-column prop="drug_name" label="药品" min-width="120" />
          <el-table-column prop="status_label" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row._status === 'new' ? 'success' : row._status === 'changed' ? 'warning' : row._status === 'removed' ? 'danger' : 'info'" size="small">
                {{ row.status_label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="本次" min-width="160">
            <template #default="{ row }">
              <span v-if="row._status !== 'removed'">
                {{ row.curr_dosage }}
                <span v-if="row.curr_specification" style="font-size:12px;color:var(--text-secondary);"> / {{ row.curr_specification }}</span>
              </span>
              <span v-else style="color:var(--text-secondary);">-</span>
            </template>
          </el-table-column>
          <el-table-column label="上次" min-width="160">
            <template #default="{ row }">
              <span v-if="row._status !== 'new'">
                {{ row.prev_dosage }}
                <span v-if="row.prev_specification" style="font-size:12px;color:var(--text-secondary);"> / {{ row.prev_specification }}</span>
              </span>
              <span v-else style="color:var(--text-secondary);">-</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <div v-else style="text-align:center;padding:30px;color:var(--text-secondary);">
        这是该患者的第一条用药记录，无历史数据可对比。
      </div>
      <template #footer>
        <el-button @click="compareVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { listMedications, getMedication, createMedication, deleteMedication } from '../api/index'
import type { MedicationRecordCreate } from '../api/index'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const records = ref<any[]>([])
const loaded = ref(false)
const formVisible = ref(false)
const detailVisible = ref(false)
const compareVisible = ref(false)
const detail = ref<any>({})
const editingId = ref<number | null>(null)
const submitting = ref(false)
const compareItems = ref<any[]>([])
const compareRecord = ref<any>(null)
const comparePrev = ref<any>(null)

interface DrugItem {
  drug_name: string
  specification: string
  dosage: string
  usage_method: string
  notes: string
}

const form = ref<{
  doctor: string
  start_date: string | null
  notes: string
  items: DrugItem[]
}>({
  doctor: '',
  start_date: null,
  notes: '',
  items: [],
})

const displayCompareItems = computed(() =>
  compareItems.value.map((item: any) => ({
    ...item,
    _status: item.status,
    status_label: item.status === 'new' ? '新增' : item.status === 'changed' ? '变更' : item.status === 'removed' ? '停用' : '不变',
  }))
)

async function loadData() {
  if (!authStore.currentPatient) {
    records.value = []
    loaded.value = false
    return
  }
  try {
    const res = await listMedications(authStore.currentPatient.id)
    records.value = res.data
    loaded.value = true
  } catch {
    ElMessage.error('加载失败')
  }
}

function openCreate() {
  editingId.value = null
  form.value = { doctor: '', start_date: null, notes: '', items: [] }
  formVisible.value = true
}

function addDrug() {
  form.value.items.push({ drug_name: '', specification: '', dosage: '', usage_method: '', notes: '' })
}

function removeDrug(idx: number) {
  form.value.items.splice(idx, 1)
}

async function doSubmit() {
  if (!authStore.currentPatient) return
  if (!form.value.doctor) { ElMessage.warning('请填写开药医生'); return }
  if (form.value.items.length === 0) { ElMessage.warning('请至少添加一种药品'); return }

  submitting.value = true
  try {
    const payload: MedicationRecordCreate = {
      patient_id: authStore.currentPatient.id,
      doctor: form.value.doctor,
      start_date: form.value.start_date || undefined,
      notes: form.value.notes || undefined,
      items: form.value.items.map((d) => ({
        drug_name: d.drug_name,
        specification: d.specification,
        dosage: d.dosage,
        usage_method: d.usage_method,
        notes: d.notes,
      })),
    }

    if (editingId.value) {
      await createMedication(payload)
    } else {
      const res = await createMedication(payload)
      compareItems.value = res.data.compared_items || []
      compareRecord.value = res.data.record
      comparePrev.value = res.data.prev_record
      if (compareItems.value.length > 0) {
        formVisible.value = false
        compareVisible.value = true
      }
    }

    if (!editingId.value && compareItems.value.length === 0) {
      formVisible.value = false
      ElMessage.success('保存成功')
    }

    await loadData()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

async function viewDetail(id: number) {
  try {
    const res = await getMedication(id)
    detail.value = res.data
    detailVisible.value = true
  } catch {
    ElMessage.error('加载失败')
  }
}

async function doDelete(id: number) {
  try {
    await deleteMedication(id)
    ElMessage.success('删除成功')
    await loadData()
  } catch {
    ElMessage.error('删除失败')
  }
}

watch(() => authStore.currentPatient, (np) => {
  if (np) loadData()
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
