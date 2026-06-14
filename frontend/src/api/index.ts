import api from './client'

export interface ResultItem {
  metric_name: string
  value: number
  unit?: string
  ref_min?: number | null
  ref_max?: number | null
  notes?: string
}

export interface ReportCreate {
  patient_id: number
  institution: string
  exam_date: string
  results: ResultItem[]
  notes?: string
}

export interface TemplateItemData {
  metric_name: string
  unit: string
  ref_min?: number | null
  ref_max?: number | null
  notes?: string | null
}

export function listReports(patientId?: number, page = 1, size = 20, extra?: Record<string, any>) {
  const params: Record<string, any> = { page, size }
  if (patientId) params.patient_id = patientId
  if (extra) Object.assign(params, extra)
  return api.get('/api/reports/', { params })
}

export function getReport(id: number) {
  return api.get(`/api/reports/${id}`)
}

export function createReport(data: ReportCreate) {
  return api.post('/api/reports/', data)
}

export function updateReport(id: number, data: Partial<ReportCreate>) {
  return api.put(`/api/reports/${id}`, data)
}

export function deleteReport(id: number) {
  return api.delete(`/api/reports/${id}`)
}

export function getCatalog() {
  return api.get('/api/metrics/catalog')
}

export function normalizeMetric(rawName: string) {
  return api.get('/api/metrics/normalize', { params: { raw_name: rawName } })
}

export function getPresetTemplates() {
  return api.get('/api/metrics/templates/presets')
}

export function listTemplates() {
  return api.get('/api/metrics/templates')
}

export function createTemplate(data: { name: string; items: TemplateItemData[] }) {
  return api.post('/api/metrics/templates', data)
}

export function updateTemplate(id: number, data: { name?: string; items?: TemplateItemData[] }) {
  return api.put(`/api/metrics/templates/${id}`, data)
}

export function deleteTemplate(id: number) {
  return api.delete(`/api/metrics/templates/${id}`)
}

export function getTrend(metricName: string, patientId: number, rangeMonths?: number) {
  const params: Record<string, any> = { patient_id: patientId, metric_name: metricName }
  if (rangeMonths) params.range = rangeMonths
  return api.get('/api/trends/', { params })
}

export function getDashboard(patientId: number) {
  return api.get(`/api/dashboard/${patientId}`)
}

export function generateShare(data: { patient_id: number; metric_names?: string[]; expire_days?: number }) {
  return api.post('/api/share/generate', data)
}

export interface MedicationItemData {
  drug_name: string
  specification: string
  dosage: string
  usage_method: string
  notes?: string | null
}

export interface MedicationRecordCreate {
  patient_id: number
  doctor: string
  start_date?: string | null
  notes?: string | null
  items: MedicationItemData[]
}

export function listMedications(patientId: number) {
  return api.get('/api/medications/', { params: { patient_id: patientId } })
}

export function getMedication(id: number) {
  return api.get(`/api/medications/${id}`)
}

export function createMedication(data: MedicationRecordCreate) {
  return api.post('/api/medications/', data)
}

export function updateMedication(id: number, data: Partial<MedicationRecordCreate>) {
  return api.put(`/api/medications/${id}`, data)
}

export function deleteMedication(id: number) {
  return api.delete(`/api/medications/${id}`)
}

export function getMedicationTimeline(patientId: number) {
  return api.get(`/api/medications/timeline/${patientId}`)
}

export function listMetricsWithAbnormalCount(patientId: number) {
  return api.get(`/api/trends/metrics?patient_id=${patientId}`)
}
