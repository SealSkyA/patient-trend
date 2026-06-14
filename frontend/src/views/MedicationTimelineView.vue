<template>
  <div class="page-container">
    <div class="page-header">
      <h2>药物周期</h2>
      <p>追踪每种药物的开始、变更和停用历程</p>
    </div>

    <el-card style="margin-bottom:20px;">
      <el-input
        v-model="searchText"
        placeholder="搜索药物名称..."
        clearable
        size="default"
        prefix-icon="Search"
        style="max-width:320px;"
        @input="onSearch"
      />
    </el-card>

    <div v-if="filteredEntries.length === 0 && loaded" class="empty-state">
      <div class="icon">&#x1f48a;</div>
      <p>暂无用药记录</p>
    </div>

    <div v-else class="timeline">
      <div
        v-for="(group, gi) in groupedEntries"
        :key="gi"
        class="timeline-group"
      >
        <div class="timeline-date">{{ group.date }}</div>

        <div
          v-for="(entry, ei) in group.entries"
          :key="ei"
          class="timeline-item"
          :class="{
            'is-new': entry.status === 'new',
            'is-changed': entry.status === 'changed',
            'is-removed': entry.status === 'removed',
          }"
        >
          <div class="timeline-dot">
            <div class="dot-inner" />
          </div>

          <div class="timeline-card">
            <div class="tc-header">
              <span class="tc-doctor">{{ entry.doctor }}</span>
              <el-tag
                size="small"
                :type="entry.status === 'new' ? 'success' : entry.status === 'changed' ? 'warning' : entry.status === 'removed' ? 'danger' : 'info'"
                effect="plain"
              >
                {{ entry.status === 'new' ? '开新药' : entry.status === 'changed' ? '用量变化' : entry.status === 'removed' ? '停用' : '不变' }}
              </el-tag>
            </div>

            <div class="tc-body">
              <span class="tc-drug">{{ entry.drug_name }}</span>
              <span class="tc-dosage">{{ entry.dosage }}</span>
              <span v-if="entry.specification" class="tc-spec"> / {{ entry.specification }}</span>
              <span v-if="entry.usage_method" class="tc-usage"> &middot; {{ entry.usage_method }}</span>
            </div>

            <div v-if="entry.status === 'changed' && entry.prev_dosage" class="tc-change">
              <span class="arrow-prev">{{ entry.prev_dosage }}</span>
              <span class="arrow-icon">&rarr;</span>
              <span class="arrow-curr">{{ entry.dosage }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getMedicationTimeline } from '../api/index'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const entries = ref<any[]>([])
const loaded = ref(false)
const searchText = ref('')

async function loadData() {
  if (!authStore.currentPatient) {
    entries.value = []
    loaded.value = false
    return
  }
  try {
    const res = await getMedicationTimeline(authStore.currentPatient.id)
    entries.value = res.data.entries || []
    loaded.value = true
  } catch {
    ElMessage.error('加载失败')
  }
}

const filteredEntries = computed(() => {
  const q = searchText.value.trim().toLowerCase()
  if (!q) return entries.value
  return entries.value.filter((e: any) =>
    e.drug_name.toLowerCase().includes(q) || e.doctor.toLowerCase().includes(q)
  )
})

const groupedEntries = computed(() => {
  const map: Record<string, any[]> = {}
  for (const e of filteredEntries.value) {
    if (!map[e.date]) map[e.date] = []
    map[e.date].push(e)
  }
  return Object.entries(map)
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([date, items]) => ({ date, entries: items }))
})

function onSearch() {}

watch(() => authStore.currentPatient, (np) => {
  if (np) loadData()
}, { immediate: true })
</script>

<style scoped>
.timeline {
  position: relative;
  padding-left: 0;
}

.timeline-group {
  position: relative;
  padding-left: 44px;
}

.timeline-date {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
  padding: 18px 0 8px;
  position: relative;
}
.timeline-date::before {
  content: '';
  position: absolute;
  left: -30px;
  top: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #6366f1;
  border: 3px solid #eef2ff;
  transform: translateY(-50%);
  z-index: 1;
}

.timeline-group::before {
  content: '';
  position: absolute;
  left: 16px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, #e2e8f0 0%, #cbd5e1 100%);
}

.timeline-item {
  position: relative;
  padding: 8px 0;
}

.timeline-dot {
  position: absolute;
  left: -44px;
  top: 22px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}
.is-new .timeline-dot { background: #d1fae5; }
.is-changed .timeline-dot { background: #fef3c7; }
.is-removed .timeline-dot { background: #fee2e2; }
.is-unchanged .timeline-dot,
.timeline-dot { background: #f1f5f9; }

.dot-inner {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.is-new .dot-inner { background: #10b981; }
.is-changed .dot-inner { background: #f59e0b; }
.is-removed .dot-inner { background: #ef4444; }
.is-unchanged .dot-inner { background: #94a3b8; }

.timeline-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04);
  transition: box-shadow 0.15s;
}
.timeline-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 0 0 1px rgba(99,102,241,0.2);
}

.tc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
  flex-wrap: wrap;
}

.tc-doctor {
  font-size: 13px;
  color: var(--text-secondary);
}

.tc-body {
  font-size: 16px;
  line-height: 1.5;
}

.tc-drug {
  font-weight: 700;
  color: var(--text);
}

.tc-dosage {
  font-weight: 600;
  color: var(--primary);
  margin-left: 8px;
}

.tc-spec {
  font-size: 13px;
  color: var(--text-secondary);
}

.tc-usage {
  font-size: 13px;
  color: var(--text-secondary);
}

.tc-change {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  background: #fef3c7;
  border-radius: 6px;
  padding: 4px 10px;
  display: inline-flex;
}

.arrow-prev {
  color: #92400e;
  text-decoration: line-through;
}

.arrow-icon {
  color: #f59e0b;
  font-weight: 700;
}

.arrow-curr {
  color: #b45309;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}
.empty-state .icon {
  font-size: 48px;
  margin-bottom: 12px;
}

@media (max-width: 768px) {
  .timeline {
    padding-left: 0;
  }
  .timeline-group {
    padding-left: 36px;
  }
  .timeline-group::before {
    left: 12px;
  }
  .timeline-date::before {
    left: -24px;
    width: 10px;
    height: 10px;
  }
  .timeline-dot {
    left: -36px;
    width: 24px;
    height: 24px;
  }
  .dot-inner {
    width: 8px;
    height: 8px;
  }
  .timeline-card {
    padding: 12px 14px;
  }
  .tc-body {
    font-size: 14px;
  }
}
</style>
