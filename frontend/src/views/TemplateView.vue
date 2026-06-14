<template>
  <div class="page-container">
    <div class="page-header">
      <h2>模板管理</h2>
      <p>自定义检查模板，录入更快更准</p>
    </div>

    <el-card>
      <template #header>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
          <span>我的模板</span>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <el-input
              v-model="searchText"
              placeholder="搜索模板名称或指标"
              size="small"
              clearable
              style="width:200px;"
              @input="filterTemplates"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" size="small" @click="openCreate">
              <el-icon style="margin-right:4px;"><Plus /></el-icon> 创建模板
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="customTemplates.length === 0" class="empty-state">
        <div class="icon">📋</div>
        <p>暂未创建自定义模板</p>
        <el-button type="primary" size="small" @click="openCreate" style="margin-top:8px;">
          创建第一个模板
        </el-button>
      </div>

      <div v-else style="display:flex;flex-direction:column;gap:12px;">
        <div
          v-for="t in filteredTemplates"
          :key="t.id"
          class="template-card"
        >
          <div class="template-header" @click="toggleCollapse(t.id)">
            <div style="display:flex;align-items:center;gap:8px;">
              <el-icon :size="18" style="cursor:pointer;transition:transform 0.3s;" :class="{ 'collapsed': collapsedIds.includes(t.id) }">
                <ArrowRight />
              </el-icon>
              <div>
                <div class="template-name">{{ t.name }}</div>
                <div class="template-meta">
                  {{ t.items?.length || 0 }} 项指标
                  <span style="margin-left:8px;color:var(--text-secondary);">
                    创建于 {{ formatDate(t.created_at) }}
                  </span>
                </div>
              </div>
            </div>
            <div class="template-actions">
              <el-button size="small" @click.stop="openEdit(t)">编辑</el-button>
              <el-popconfirm title="确定删除此模板？" @confirm="doDelete(t.id)">
                <template #reference>
                  <el-button size="small" type="danger" plain>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
          <div v-show="!collapsedIds.includes(t.id)" style="margin-top:12px;">
            <el-table :data="t.items" size="small" border style="margin-top:12px;">
              <el-table-column type="index" label="序号" width="60" align="center" />
              <el-table-column prop="metric_name" label="指标名称" min-width="150" />
              <el-table-column prop="unit" label="单位" width="80" />
              <el-table-column label="参考区间" width="160">
                <template #default="{ row }">
                  <template v-if="row.ref_min != null || row.ref_max != null">
                    {{ row.ref_min ?? '--' }} ~ {{ row.ref_max ?? '--' }}
                  </template>
                  <span v-else style="color:var(--text-secondary);">未设置</span>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />
            </el-table>
          </div>
        </div>
      </div>
    </el-card>

    <el-drawer
      v-model="formVisible"
      :title="editingId ? '编辑模板' : '创建模板'"
      size="90%"
      :close-on-click-modal="false"
      class="template-drawer"
    >
      <div style="padding:0 20px;">
        <el-form :model="tplForm" label-position="top">
          <el-form-item label="模板名称" required>
            <el-input v-model="tplForm.name" placeholder="例如：入职体检" size="large" />
          </el-form-item>
        </el-form>

        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <span style="font-weight:600;font-size:15px;">模板指标</span>
          <el-button type="primary" size="small" plain @click="addRow">
            <el-icon style="margin-right:4px;"><Plus /></el-icon> 添加指标
          </el-button>
        </div>

        <el-table :data="tplForm.items" size="small" border style="margin-bottom:16px;">
          <el-table-column type="index" label="序号" width="60" align="center" />
          <el-table-column label="指标名称" min-width="200">
            <template #default="{ row }">
              <el-input v-model="row.metric_name" placeholder="例如：血糖 - 空腹" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="单位" width="100">
            <template #default="{ row }">
              <el-input v-model="row.unit" placeholder="mmol/L" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="参考下限" width="110">
            <template #default="{ row }">
              <el-input v-model.number="row.ref_min" type="number" placeholder="min" size="small" :controls="false" />
            </template>
          </el-table-column>
          <el-table-column label="参考上限" width="110">
            <template #default="{ row }">
              <el-input v-model.number="row.ref_max" type="number" placeholder="max" size="small" :controls="false" />
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="150">
            <template #default="{ row }">
              <el-input v-model="row.notes" placeholder="注意事项" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="center">
            <template #default="{ $index }">
              <el-button size="small" type="primary" link @click="moveRow($index, 'up')" :disabled="$index === 0">
                <el-icon><Top /></el-icon>
              </el-button>
              <el-button size="small" type="primary" link @click="moveRow($index, 'down')" :disabled="$index === tplForm.items.length - 1">
                <el-icon><Bottom /></el-icon>
              </el-button>
              <el-button size="small" type="danger" link @click="removeRow($index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div
          v-for="(row, idx) in tplForm.items"
          :key="idx"
          style="background:var(--bg);border-radius:var(--radius-sm);padding:16px;margin-bottom:12px;position:relative;"
        >
          <el-button
            style="position:absolute;top:8px;right:8px;"
            type="danger"
            link
            size="small"
            @click="removeRow(idx)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>

          <el-row :gutter="12">
            <el-col :xs="12" :sm="12">
              <el-form-item label="指标名称" label-position="top" style="margin-bottom:10px;">
                <el-input v-model="row.metric_name" placeholder="血糖-空腹" />
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-form-item label="单位" label-position="top" style="margin-bottom:10px;">
                <el-input v-model="row.unit" placeholder="mmol/L" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12">
            <el-col :xs="12" :sm="6">
              <el-form-item label="参考下限" label-position="top" style="margin-bottom:10px;">
                <el-input v-model.number="row.ref_min" type="number" placeholder="最小值" :controls="false" />
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-form-item label="参考上限" label-position="top" style="margin-bottom:10px;">
                <el-input v-model.number="row.ref_max" type="number" placeholder="最大值" :controls="false" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="备注" label-position="top" style="margin-bottom:0;">
            <el-input v-model="row.notes" placeholder="注意事项、检查要求等" />
          </el-form-item>
        </div>
      </div>

      <template #footer>
        <div style="padding:0 20px;">
          <el-button @click="formVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTemplate" :loading="saving">
            {{ editingId ? '更新模板' : '创建模板' }}
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listTemplates, createTemplate, updateTemplate, deleteTemplate } from '../api/index'
import { ElMessage } from 'element-plus'
import { Plus, Delete, ArrowRight, Top, Bottom, Search } from '@element-plus/icons-vue'

const customTemplates = ref<any[]>([])
const filteredTemplates = ref<any[]>([])
const collapsedIds = ref<number[]>([])
const searchText = ref('')
const formVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const tplForm = reactive({
  name: '',
  items: [] as any[],
})

function filterTemplates() {
  if (!searchText.value.trim()) {
    filteredTemplates.value = customTemplates.value
  } else {
    const term = searchText.value.toLowerCase()
    filteredTemplates.value = customTemplates.value.filter(t => {
      if (t.name.toLowerCase().includes(term)) return true
      if (t.items?.some((i: any) => i.metric_name.toLowerCase().includes(term))) return true
      return false
    })
  }
}

function toggleCollapse(id: number) {
  const idx = collapsedIds.value.indexOf(id)
  if (idx >= 0) {
    collapsedIds.value.splice(idx, 1)
  } else {
    collapsedIds.value.push(id)
  }
}

function formatDate(d: string) {
  if (!d) return ''
  return d.split('T')[0]
}

function openCreate() {
  editingId.value = null
  tplForm.name = ''
  tplForm.items = []
  formVisible.value = true
}

function openEdit(tpl: any) {
  editingId.value = tpl.id
  tplForm.name = tpl.name
  tplForm.items = (tpl.items || []).map((i: any, idx: number) => ({
    metric_name: i.metric_name,
    unit: i.unit || '',
    ref_min: i.ref_min ?? null,
    ref_max: i.ref_max ?? null,
    notes: i.notes || '',
    sort_order: i.sort_order ?? idx,
  })).sort((a: any, b: any) => (a.sort_order || 0) - (b.sort_order || 0))
  formVisible.value = true
}

function addRow() {
  const nextOrder = tplForm.items.length > 0 ? (tplForm.items[tplForm.items.length - 1].sort_order || tplForm.items.length - 1) + 1 : 0
  tplForm.items.push({
    metric_name: '',
    unit: '',
    ref_min: null,
    ref_max: null,
    notes: '',
    sort_order: nextOrder,
  })
}

function moveRow(idx: number, direction: 'up' | 'down') {
  const targetIdx = direction === 'up' ? idx - 1 : idx + 1
  if (targetIdx < 0 || targetIdx >= tplForm.items.length) return
  const temp = tplForm.items[idx]
  tplForm.items[idx] = tplForm.items[targetIdx]
  tplForm.items[targetIdx] = temp
  tplForm.items.forEach((item, i) => {
    item.sort_order = i
  })
}

function removeRow(idx: number) {
  tplForm.items.splice(idx, 1)
  tplForm.items.forEach((item, i) => {
    item.sort_order = i
  })
}

async function saveTemplate() {
  if (!tplForm.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  const validItems = tplForm.items.filter(i => i.metric_name.trim())
  if (validItems.length === 0) {
    ElMessage.warning('请至少添加一个指标')
    return
  }

  saving.value = true
  try {
    const payload = {
      name: tplForm.name.trim(),
      items: validItems
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
        .map(i => ({
          metric_name: i.metric_name.trim(),
          unit: i.unit || '',
          ref_min: i.ref_min != null ? Number(i.ref_min) : null,
          ref_max: i.ref_max != null ? Number(i.ref_max) : null,
          notes: i.notes || null,
          sort_order: i.sort_order ?? 0,
        })),
    }

    if (editingId.value) {
      await updateTemplate(editingId.value, payload)
      ElMessage.success('模板更新成功')
    } else {
      await createTemplate(payload)
      ElMessage.success('模板创建成功')
    }
    formVisible.value = false
    await loadAll()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function doDelete(id: number) {
  try {
    await deleteTemplate(id)
    ElMessage.success('删除成功')
    await loadAll()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function loadAll() {
  try {
    const res = await listTemplates()
    customTemplates.value = res.data || []
    filteredTemplates.value = customTemplates.value
  } catch {}
}

onMounted(loadAll)
</script>

<style scoped>
.template-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}

.template-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  cursor: pointer;
}

.template-header .el-icon {
  transition: transform 0.3s;
}

.template-header .el-icon.collapsed {
  transform: rotate(0deg);
}

.template-header:not(.collapsed) .el-icon {
  transform: rotate(90deg);
}

.template-name {
  font-size: 16px;
  font-weight: 600;
}

.template-meta {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.template-actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .template-header {
    flex-direction: column;
  }

  .template-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .template-drawer :deep(.el-drawer__body) {
    padding: 10px;
  }
  
  .el-table {
    font-size: 12px;
  }
  
  .el-table .el-button {
    padding: 4px 6px;
  }
}
</style>
