import api from './client'

export interface PatientCreate {
  name: string
  gender?: string
  birth_date?: string
}

export function listPatients() {
  return api.get('/api/patients/')
}

export function createPatient(data: PatientCreate) {
  return api.post('/api/patients/', data)
}

export function updatePatient(id: number, data: Partial<PatientCreate>) {
  return api.put(`/api/patients/${id}`, data)
}

export function deletePatient(id: number) {
  return api.delete(`/api/patients/${id}`)
}
