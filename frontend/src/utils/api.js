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
export const getPosicionIva = (periodo) => api.get('/iva/posicion', { params: { periodo } })

// ─── Facturas ─────────────────────────────────────────────────────────────────
export const getFacturas = (params) => api.get('/facturas/', { params })
export const getFactura = (id) => api.get(`/facturas/${id}`)
export const createFactura = (data) => api.post('/facturas/', data)
export const getFacturaSummary = (clientId, year) =>
  api.get(`/facturas/summary/${clientId}`, { params: { year } })


// ─── Retenciones / Percepciones (Mis Retenciones ARCA) ───────────────────────
export const syncRetenciones = (data) => api.post('/retenciones/sync', data)
export const getRetencionSyncJob = (jobId) => api.get(`/retenciones/sync/${jobId}`)
export const getRetenciones = (params) => api.get('/retenciones/', { params })
export const getRetencionesSummary = (clientId, period) =>
  api.get(`/retenciones/summary/${clientId}`, { params: { period } })
export const deleteRetencion = (id) => api.delete(`/retenciones/${id}`)

// ─── Comprobantes Recibidos + Cruce (R-05) ───────────────────────────────────
export const syncComprobantes = (data) => api.post('/comprobantes/sync', data)
export const getComprobantes = (params) => api.get('/comprobantes/', { params })
export const getCruce = (clientId, period) =>
  api.get('/comprobantes/cruce', { params: { client_id: clientId, period } })
export const exportHolistor = (clientId, period) =>
  api.get('/comprobantes/export-holistor', {
    params: { client_id: clientId, period },
    responseType: 'blob',
  })
export const deleteComprobante = (id) => api.delete(`/comprobantes/${id}`)
// ─── Cuentas Corrientes ───────────────────────────────────────────────────────
export const getMovimientosCC = (clientId) => api.get(`/cuentas-corrientes/client/${clientId}`)
export const getSaldoCC = (clientId) => api.get(`/cuentas-corrientes/client/${clientId}/saldo`)
export const createMovimientoCC = (data) => api.post('/cuentas-corrientes/', data)

// ─── R-03: Honorarios ────────────────────────────────────────────────────────
export const getProductosReferencia = () => api.get('/honorarios/productos-referencia')
export const createProducto = (data) => api.post('/honorarios/productos-referencia', data)
export const updateProducto = (id, data) => api.put(`/honorarios/productos-referencia/${id}`, data)
export const configurarHonorario = (clientId, data) => api.put(`/honorarios/clientes/${clientId}/configurar`, data)
export const getHonorarios = (params) => api.get('/honorarios/', { params })
export const calcularHonorario = (clientId, period) => api.post(`/honorarios/calcular/${clientId}/${period}`)
export const calcularPeriodo = (period) => api.post(`/honorarios/calcular-periodo/${period}`)
export const getPreviewActualizacion = (pct) =>
  api.get('/honorarios/actualizacion-cuatrimestral/preview', { params: { indice_pct: pct } })
export const aplicarActualizacion = (data) => api.post('/honorarios/actualizacion-cuatrimestral/aplicar', data)

// ─── R-04: Profesionales, Pagos, Liquidaciones ───────────────────────────────
export const getProfesionales = (params) => api.get('/profesionales/', { params })
export const createProfesional = (data) => api.post('/profesionales/', data)
export const updateProfesional = (id, data) => api.put(`/profesionales/${id}`, data)
export const getPagos = (params) => api.get('/profesionales/pagos', { params })
export const createPago = (data) => api.post('/profesionales/pagos', data)
export const deletePago = (id) => api.delete(`/profesionales/pagos/${id}`)
export const getLiquidacion = (profesionalId, period) =>
  api.get(`/profesionales/liquidaciones/${profesionalId}/${period}`)
export const setLiquidacionHonorarios = (profesionalId, period, data) =>
  api.put(`/profesionales/liquidaciones/${profesionalId}/${period}/honorarios`, data)
export const addReintegro = (profesionalId, period, data) =>
  api.post(`/profesionales/liquidaciones/${profesionalId}/${period}/reintegros`, data)
export const deleteReintegro = (profesionalId, period, reintegroId) =>
  api.delete(`/profesionales/liquidaciones/${profesionalId}/${period}/reintegros/${reintegroId}`)
export const cerrarLiquidacion = (profesionalId, period, data) =>
  api.post(`/profesionales/liquidaciones/${profesionalId}/${period}/cerrar`, data)


// ─── F2-02: Cobros (endpoint dedicado /pagos/) ────────────────────────────────
export const registrarCobro = (data) => api.post('/pagos/', data)
export const getPagosRegistrados = (params) => api.get('/pagos/', { params })
export const getPagoById = (id) => api.get(`/pagos/${id}`)

// ─── F2-05: Billetes en caja ──────────────────────────────────────────────────
export const getBilletesStock = () => api.get('/billetes/')
export const registrarMovimientoBillete = (data) => api.post('/billetes/movimiento', data)

// ─── F3 (R-12): Retiros de socios ────────────────────────────────────────────
export const getRetiros = (params) => api.get('/retiros/', { params })
export const getRetiroById = (id) => api.get(`/retiros/${id}`)
export const crearRetiro = (data) => api.post('/retiros/', data)

// ─── F3 (R-11): Flujo de fondos ──────────────────────────────────────────────
export const getFlujoFondosMensual = (periodo, profesionalId) =>
  api.get('/flujo-fondos/', { params: { periodo, profesional_id: profesionalId || undefined } })
export const getFlujoFondosAnual = (year, profesionalId) =>
  api.get('/flujo-fondos/anual', { params: { year, profesional_id: profesionalId || undefined } })
export const verificarConsistenciaFlujo = (periodo, tolerancia) =>
  api.get('/flujo-fondos/verificar-consistencia', { params: { periodo, tolerancia } })

// ─── F3 (R-13): Actualización cuatrimestral con índice ────────────────────────
export const previewActualizacionHonorarios = (data) =>
  api.post('/honorarios/preview-actualizacion', data)
export const aplicarActualizacionHonorarios = (data) =>
  api.post('/honorarios/aplicar-actualizacion', data)

// ─── F2-11: Liquidaciones preview ────────────────────────────────────────────
export const getLiquidacionPreview = (profesionalId, periodo) =>
  api.get(`/profesionales/liquidaciones/${profesionalId}/preview`, { params: { periodo } })
export const getLiquidacionesPreviewAll = (periodo) =>
  api.get('/profesionales/liquidaciones/preview', { params: { periodo } })
export const getLiquidaciones = (params) => api.get('/profesionales/liquidaciones', { params })
// ─── R-10: Generación HWCRARCA ────────────────────────────────────────────────
export const generarHwcrarca = (limpiezaId) =>
  api.post(`/herramientas/${limpiezaId}/generar-hwcrarca`, null, { responseType: 'blob' })

// ─── R-09: Maestro de Proveedores / Imputación ────────────────────────────────
export const resolverImputacion = (cuit) => api.get(`/imputacion/cuit/${cuit}`)
export const getProveedores = (params) => api.get('/imputacion/proveedores', { params })
export const createProveedor = (data) => api.post('/imputacion/proveedores', data)
export const updateProveedor = (id, data) => api.put(`/imputacion/proveedores/${id}`, data)
export const deleteProveedor = (id) => api.delete(`/imputacion/proveedores/${id}`)

// ─── R-15: Conciliación bancaria (Fase 3) ────────────────────────────────────
export const importarExtracto = (formData) =>
  api.post('/conciliacion/import-extracto', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
export const getExtractos = (params) => api.get('/conciliacion/extractos', { params })
export const getMovimientosExtracto = (extractoId, params) =>
  api.get(`/conciliacion/extracto/${extractoId}/movimientos`, { params })
export const runMatching = (extractoId) =>
  api.post(`/conciliacion/${extractoId}/run-matching`)
export const matchManual = (movimientoId, data) =>
  api.post(`/conciliacion/movimiento/${movimientoId}/match-manual`, data)
export const desconciliarMovimiento = (movimientoId) =>
  api.post(`/conciliacion/movimiento/${movimientoId}/desconciliar`)
export const sugerenciasMovimiento = (movimientoId, topN = 3) =>
  api.get(`/conciliacion/movimiento/${movimientoId}/sugerencias`, { params: { top_n: topN } })
