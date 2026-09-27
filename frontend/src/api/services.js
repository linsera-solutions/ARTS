import { apiClient } from './client'

export const healthService = {
  getHealth: () => apiClient.get('/health'),
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
}

export const applicationsService = {
  list: (params) => apiClient.get('/applications', params),
  get: (id) => apiClient.get(`/applications/${id}`),
  create: (data) => apiClient.post('/applications', data),
  updateStatus: (id, data) => apiClient.patch(`/applications/${id}/status`, data),
}

export const evaluationsService = {
  listByApplication: (applicationId) => apiClient.get('/evaluations', { application_id: applicationId }),
  get: (id) => apiClient.get(`/evaluations/${id}`),
  create: (data) => apiClient.post('/evaluations', data),
  update: (id, data) => apiClient.patch(`/evaluations/${id}`, data),
}

export const interviewsService = {
  listByApplication: (applicationId) => apiClient.get('/interviews', { application_id: applicationId }),
  get: (id) => apiClient.get(`/interviews/${id}`),
  create: (data) => apiClient.post('/interviews', data),
  update: (id, data) => apiClient.patch(`/interviews/${id}`, data),
}

export const notesService = {
  listByEntity: (entityType, entityId) =>
    apiClient.get('/notes', { entity_type: entityType, entity_id: entityId }),
  create: (data) => apiClient.post('/notes', data),
  delete: (id) => apiClient.delete(`/notes/${id}`),
}
