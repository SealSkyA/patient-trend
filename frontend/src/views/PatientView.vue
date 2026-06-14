<template>
  <div class="page-container">
    <div class="page-header">
      <h2>患者管理</h2>
      <p>管理患者信息，添加、编辑或删除</p>
    </div>

    <el-card>
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
        <el-input
          v-model="search"
          placeholder="搜索患者..."
          prefix-icon="Search"
          style="width:240px;"
          size="default"
          clearable
        />
        <el-button type="primary" size="small" @click="openForm()">
          <el-icon style="margin-right:4px;"><Plus /></el-icon> 添加患者
        </el-button>
      </div>

      <el-table :data="filteredPatients" size="default" stripe style="width:100%;">
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column prop="gender" label="性别" width="80" align="center" />
        <el-table-column label="出生日期" width="130">
          <template #default="{ row }">{{ row.birth_date || '-' }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <div style="display:flex;flex-direction:column;gap:4px;">
              <el-button size="small" link @click="openForm(row)">编辑</el-button>
              <el-popconfirm title="确定删除？关联报告将一并删除" @confirm="doDelete(row.id)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="patients.length === 0 && loaded" class="empty-state">
        <div class="icon">👤</div>
        <p>暂无患者信息</p>
        <el-button type="primary" @click="openForm()" style="margin-top:12px;">添加第一个患者</el-button>
      </div>
    </el-card>

    <el-dialog v-model="formVisible" :title="editingId ? '编辑患者' : '添加患者'" width="460px" :close-on-click-modal="false">
      <el-form :model="pfForm" label-position="top">
        <el-form-item label="姓名" required>
          <el-input v-model="pfForm.name" placeholder="患者姓名" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="pfForm.gender" style="width:100%;" placeholder="选择性别" clearable>
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="pfForm.birth_date" type="date" value-format="YYYY-MM-DD" style="width:100%;" placeholder="选择日期" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="savePatient" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { listPatients, createPatient, updatePatient, deletePatient } from '../api/patients'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const patients = ref<any[]>([])
const loaded = ref(false)
const search = ref('')
const formVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const pfForm = reactive({ name: '', gender: '', birth_date: '' })

const filteredPatients = computed(() => {
  if (!search.value) return patients.value
  const kw = search.value.toLowerCase()
  return patients.value.filter((p: any) =>
    p.name.toLowerCase().includes(kw)
  )
})

function formatDate(d: string) {
  if (!d) return '-'
  return d.split('T')[0]
}

async function loadPatients() {
  try {
    const res = await listPatients()
    patients.value = res.data
    authStore.patients = res.data
    loaded.value = true
  } catch {
    ElMessage.error('加载患者失败')
  }
}

function openForm(row?: any) {
  editingId.value = row?.id ?? null
  pfForm.name = row?.name ?? ''
  pfForm.gender = row?.gender ?? ''
  pfForm.birth_date = row?.birth_date ?? ''
  formVisible.value = true
}

async function savePatient() {
  if (!pfForm.name.trim()) {
    ElMessage.warning('请输入姓名')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updatePatient(editingId.value, {
        name: pfForm.name.trim(),
        gender: pfForm.gender || undefined,
        birth_date: pfForm.birth_date || undefined,
      })
      ElMessage.success('患者信息已更新')
    } else {
      await createPatient({
        name: pfForm.name.trim(),
        gender: pfForm.gender || undefined,
        birth_date: pfForm.birth_date || undefined,
      })
      ElMessage.success('患者添加成功')
    }
    formVisible.value = false
    await authStore.loadPatients()
    await loadPatients()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function doDelete(id: number) {
  try {
    await deletePatient(id)
    ElMessage.success('删除成功')
    await authStore.loadPatients()
    await loadPatients()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(loadPatients)
</script>

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
