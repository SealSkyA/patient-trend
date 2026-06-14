<template>
  <el-dialog title="选择患者" v-model="visible" append-to-body>
    <el-select v-model="selected" placeholder="请选择患者" style="width: 100%" value-key="id">
      <el-option v-for="p in authStore.patients" :key="p.id" :label="p.name" :value="p" />
    </el-select>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="selectPatient(selected)">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const selected = ref<any>(authStore.currentPatient)
const visible = ref(false)

function selectPatient(patient: any) {
  authStore.currentPatient = patient
  visible.value = false
}

function show() {
  selected.value = authStore.currentPatient
  visible.value = true
}

defineExpose({ show })
</script>
