<template>
  <div class="page-container">
    <div class="page-header">
      <h2>录入报告</h2>
      <p>快速录入检查报告数据，支持模板一键填充</p>
    </div>

    <el-card>
      <el-form :model="form" label-position="top">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="8">
            <el-form-item label="检查日期" required>
              <el-date-picker v-model="form.exam_date" type="date" value-format="YYYY-MM-DD" style="width:100%;" placeholder="选择日期" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="16">
            <el-form-item label="项目类别" required>
              <el-input v-model="form.institution" placeholder="医院/体检中心名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider border-style="dashed">
          <el-icon><Collection /></el-icon> 快捷模板
        </el-divider>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;">
          <template v-for="t in customTemplates" :key="t.id">
            <el-button size="small" type="primary" plain @click="applyCustom(t)">
              {{ t.name }} ({{ t.items?.length || 0 }}项)
            </el-button>
          </template>
          <el-button size="small" type="success" plain @click="addRow">
            <el-icon style="margin-right:4px;"><Plus /></el-icon> 手动添加
          </el-button>
        </div>

        <el-divider border-style="dashed" />

        <el-table :data="form.results" size="small" border>
          <el-table-column label="指标名称" min-width="180">
            <template #default="{ row }">
              <el-input v-model="row.metric_name" placeholder="输入指标名称" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="数值" width="110">
            <template #default="{ row }">
              <el-input v-model="row.value" type="number" step="0.01" size="small" placeholder="结果" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="90">
            <template #default="{ row }">
              <el-input v-model="row.unit" size="small" placeholder="单位" />
            </template>
          </el-table-column>
          <el-table-column label="参考下限" width="100">
            <template #default="{ row }">
              <el-input v-model.number="row.ref_min" type="number" size="small" placeholder="min" :controls="false" />
            </template>
          </el-table-column>
          <el-table-column label="参考上限" width="100">
            <template #default="{ row }">
              <el-input v-model.number="row.ref_max" type="number" size="small" placeholder="max" :controls="false" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" fixed="right" align="center">
            <template #default="{ $index }">
              <el-button size="small" type="danger" link @click="removeRow($index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-form-item label="备注" style="margin-top:16px;">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="特殊说明（如：检查前未空腹）" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            <el-icon style="margin-right:6px;"><Check /></el-icon> 保存报告
          </el-button>
          <el-button size="large" @click="clearForm">清空</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listTemplates, createReport } from '../api/index'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Check, Collection } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const submitting = ref(false)
const customTemplates = ref<any[]>([])

const form = reactive({
  exam_date: '',
  institution: '',
  results: [] as any[],
  notes: '',
})

function addRow() {
  form.results.push({ metric_name: '', value: '', unit: '', ref_min: null, ref_max: null })
}

function removeRow(idx: number) {
  form.results.splice(idx, 1)
}

function applyCustom(tpl: any) {
  form.institution = tpl.name
  form.results = (tpl.items || []).map((i: any) => ({
    metric_name: i.metric_name,
    value: '',
    unit: i.unit || '',
    ref_min: i.ref_min ?? null,
    ref_max: i.ref_max ?? null,
  }))
}

async function handleSubmit() {
  if (!authStore.currentPatient) {
    ElMessage.warning('请先选择患者')
    return
  }
  if (!form.exam_date) {
    ElMessage.warning('请选择检查日期')
    return
  }
  if (!form.institution.trim()) {
    ElMessage.warning('请填写项目类别')
    return
  }
  const validResults = form.results.filter(
    r => r.metric_name.trim() && r.value !== '' && r.value !== null
  )
  if (validResults.length === 0) {
    ElMessage.warning('请至少添加一个指标')
    return
  }

  submitting.value = true
  try {
    await createReport({
      patient_id: authStore.currentPatient.id,
      institution: form.institution.trim(),
      exam_date: form.exam_date,
      results: validResults.map(r => ({
        metric_name: r.metric_name.trim(),
        value: parseFloat(r.value),
        unit: r.unit || '',
        ref_min: r.ref_min != null ? Number(r.ref_min) : null,
        ref_max: r.ref_max != null ? Number(r.ref_max) : null,
      })),
      notes: form.notes || undefined,
    })
    ElMessage.success('报告保存成功')
    clearForm()
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    submitting.value = false
  }
}

function clearForm() {
  form.exam_date = ''
  form.institution = ''
  form.results = []
  form.notes = ''
}

onMounted(async () => {
  try {
    const res = await listTemplates()
    customTemplates.value = res.data || []
  } catch {}
})
</script>
