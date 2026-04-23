import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Flag to avoid concurrent re-validations
let _revalidating = false

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !_revalidating) {
      _revalidating = true
      // Re-validate the token before logging out.
      // A single 401 from a page-level endpoint (e.g. /clients) does NOT mean
      // the session is invalid — the token might still be good. Only log out if
      // /auth/me itself also rejects with 401.
      api.get('/auth/me')
        .catch((meErr) => {
          if (meErr.response?.status === 401) {
            window.dispatchEvent(new CustomEvent('auth:unauthorized'))
          }
        })
        .finally(() => { _revalidating = false })
    }
    return Promise.reject(err)
  }
)

export default api

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const login = (email, password) => api.post('/auth/login', { email, password })
export const getMe = () => api.get('/auth/me')

// ─── Dashboard ────────────────────────────────────────────────────────────────
export const getDashboardStats = () => api.get('/dashboard/stats')
export const getCollaboratorStats = () => api.get('/dashboard/collaborator-stats')
export const getTimeline = () => api.get('/dashboard/timeline')
export const getIvaOverview = () => api.get('/dashboard/iva-overview')
export const getTasksByType = () => api.get('/dashboard/tasks-by-type')
export const getMonthlyActivity = () => api.get('/dashboard/monthly-activity')

// ─── Clients ──────────────────────────────────────────────────────────────────
export const getClients = (params) => api.get('/clients/', { params })
export const getClient = (id) => api.get(`/clients/${id}`)
export const createClient = (data) => api.post('/clients/', data)
export const updateClient = (id, data) => api.put(`/clients/${id}`, data)
export const deleteClient = (id) => api.delete(`/clients/${id}`)
export const assignCollaborator = (clientId, collaboratorId) =>
  api.post(`/clients/${clientId}/collaborators`, { collaborator_id: collaboratorId })
export const removeCollaboratorFromClient = (clientId, collaboratorId) =>
  api.delete(`/clients/${clientId}/collaborators/${collaboratorId}`)
export const getClientCredentials = (id) => api.get(`/clients/${id}/credentials`)

// ─── Collaborators ────────────────────────────────────────────────────────────
export const getCollaborators = () => api.get('/collaborators/')
export const getAllUsers = () => api.get('/collaborators/all')
export const createCollaborator = (data) => api.post('/collaborators/', data)
export const updateCollaborator = (id, data) => api.put(`/collaborators/${id}`, data)
export const getCollaboratorStats2 = (id) => api.get(`/collaborators/${id}/stats`)

// ─── Tasks ────────────────────────────────────────────────────────────────────
export const getTasks = (params) => api.get('/tasks/', { params })
export const getTask = (id) => api.get(`/tasks/${id}`)
export const createTask = (data) => api.post('/tasks/', data)
export const updateTask = (id, data) => api.put(`/tasks/${id}`, data)
export const deleteTask = (id) => api.delete(`/tasks/${id}`)
export const createSubtask = (taskId, data) => api.post(`/tasks/${taskId}/subtasks`, data)
export const updateSubtask = (taskId, subtaskId, data) =>
  api.put(`/tasks/${taskId}/subtasks/${subtaskId}`, data)
export const deleteSubtask = (taskId, subtaskId) =>
  api.delete(`/tasks/${taskId}/subtasks/${subtaskId}`)

// ─── IVA ──────────────────────────────────────────────────────────────────────
export const getIvaRecords = (params) => api.get('/iva/', { params })
export const getIvaRecord = (id) => api.get(`/iva/${id}`)
export const createIvaRecord = (data) => api.post('/iva/', data)
export const updateIvaRecord = (id, data) => api.put(`/iva/${id}`, data)
export const fileIva = (id, vep) => api.post(`/iva/${id}/file`, null, { params: { vep_number: vep } })
export const getIvaSummary = (clientId) => api.get(`/iva/summary/${clientId}`)

// ─── Facturas ─────────────────────────────────────────────────────────────────
export const getFacturas = (params) => api.get('/facturas/', { params })
export const getFactura = (id) => api.get(`/facturas/${id}`)
export const createFactura = (data) => api.post('/facturas/', data)
export const getFacturaSummary = (clientId, year) =>
  api.get(`/facturas/summary/${clientId}`, { params: { year } })

// ─── Retenciones / Percepciones (Mis Retenciones ARCA) ───────────────────────
export const syncRetenciones = (data) => api.post('/retenciones/sync', data)
export const getRetenciones = (params) => api.get('/retenciones/', { params })
export const getRetencionesSummary = (clientId, period) =>
  api.get(`/retenciones/summary/${clientId}`, { params: { period } })
export const deleteRetencion = (id) => api.delete(`/retenciones/${id}`)
