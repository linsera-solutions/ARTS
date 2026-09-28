import { apiClient } from './client'

export const healthService = {
  getHealth: () => apiClient.get('/health'),
}

export const authService = {
  login: (credentials) => apiClient.post('/auth/login', credentials),
  getMe: () => apiClient.get('/auth/me'),
  logout: () => apiClient.post('/auth/logout'),
}


export const rolesService = {
  list: (params) => apiClient.get('/roles', params),
  get: (id) => apiClient.get(`/roles/${id}`),
  create: (data) => apiClient.post('/roles', data),
  update: (id, data) => apiClient.patch(`/roles/${id}`, data),
}

export const applicantsService = {
  list: (params) => apiClient.get('/applicants', params),
  get: (id) => apiClient.get(`/applicants/${id}`),
  create: (data) => apiClient.post('/applicants', data),
  update: (id, data) => apiClient.patch(`/applicants/${id}`, data),
  addEvidence: (id, data) => apiClient.post(`/applicants/${id}/evidence`, data),
  removeEvidence: (id, evidenceId) => apiClient.delete(`/applicants/${id}/evidence/${evidenceId}`),
  archive: (id) => apiClient.patch(`/applicants/${id}/archive`),
}

export const applicationsService = {
  list: (params) => apiClient.get('/applications', params),
  get: (id) => apiClient.get(`/applications/${id}`),
  create: (data) => apiClient.post('/applications', data),
  intake: (data) => apiClient.post('/applications/intake', data),
  batchIntake: (data) => apiClient.post('/applications/intake/batch', data),
  updateStatus: (id, data) => apiClient.patch(`/applications/${id}/status`, data),
  getAllowedTransitions: (id) => apiClient.get(`/applications/${id}/allowed-transitions`),
}

export const evaluationsService = {
  listByApplication: (applicationId) =>
    apiClient.get('/evaluations', { application_id: applicationId }),
  listCriteria: () => apiClient.get('/evaluations/criteria'),
  get: (id) => apiClient.get(`/evaluations/${id}`),
  create: (data) => apiClient.post('/evaluations', data),
  upsert: (data) => apiClient.post('/evaluations/upsert', data),
  update: (id, data) => apiClient.patch(`/evaluations/${id}`, data),
  delete: (id) => apiClient.delete(`/evaluations/${id}`),
}

export const interviewsService = {
  list: (params) => apiClient.get('/interviews', params),
  listByApplication: (applicationId) =>
    apiClient.get('/interviews', { application_id: applicationId }),
  get: (id) => apiClient.get(`/interviews/${id}`),
  create: (data) => apiClient.post('/interviews', data),
  update: (id, data) => apiClient.patch(`/interviews/${id}`, data),
}

export const notesService = {
  listByEntity: (entityType, entityId) =>
    apiClient.get('/notes', { entity_type: entityType, entity_id: entityId }),
  create: (data) => apiClient.post('/notes', data),
  update: (id, data) => apiClient.patch(`/notes/${id}`, data),
  delete: (id) => apiClient.delete(`/notes/${id}`),
}

export const intakeService = {
  webhook: (data) => apiClient.post('/intake/google-forms/webhook', data),
  csvText: (data) => apiClient.post('/intake/google-forms/csv', data),
  status: () => apiClient.get('/intake/google-sheets/status'),
  logs: (params) => apiClient.get('/intake/logs', params),
}

export const teamsService = {
  getOverview: (teamId) => apiClient.get('/teams/overview', teamId ? { team_id: teamId } : {}),
  list: () => apiClient.get('/teams'),
  get: (id) => apiClient.get(`/teams/${id}`),
  assignMember: (teamId, data) => apiClient.post(`/teams/${teamId}/members`, data),
  reassignMember: (memberId, data) => apiClient.patch(`/teams/members/${memberId}/reassign`, data),
  removeMember: (memberId, reason) => apiClient.delete(`/teams/members/${memberId}`, reason ? { reason } : {}),
}