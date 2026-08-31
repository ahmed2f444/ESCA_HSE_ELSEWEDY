import { api, agent } from './client.js'

/**
 * Every call the web client makes, in one place.
 *
 * This doubles as the frontend's half of the API contract: if a path here
 * doesn't exist in the Spring Boot OpenAPI doc, that's the integration gap.
 * Grouped by owning module so it maps 1:1 onto the team's split.
 */

const get = (url, params) => api.get(url, { params }).then((r) => r.data)
const post = (url, body) => api.post(url, body).then((r) => r.data)

export const auth = {
  login: (username, password) => post('/auth/login', { username, password }),
  me: () => get('/auth/me'),
}

const profilePath = '/users/me'
const profileShape = (data) => ({
  user_id: data.userId,
  username: data.username,
  full_name: data.fullName || '',
  email: data.email || '',
  phone: data.phone || '',
  job_title: data.jobTitle || '',
  avatar_path: data.avatarPath || null,
  zone_name: data.zoneName || '',
  department_name: data.departmentName || '',
})

export const profile = {
  get: () => get(profilePath).then(profileShape),
  update: (fields) => api.patch(profilePath, {
    fullName: fields.full_name,
    username: fields.username,
  }).then((r) => profileShape(r.data)),
  uploadAvatar: (file) => {
    const body = new FormData()
    body.append('avatar', file)
    return api.post(`${profilePath}/avatar`, body, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => profileShape(r.data))
  },
  deleteAvatar: () => api.delete(`${profilePath}/avatar`).then((r) => profileShape(r.data)),
  requestPasswordCode: () => post(`${profilePath}/password/mfa/request`, {}),
  verifyPasswordCode: (code, newPassword) =>
    api.post(`${profilePath}/password/mfa/verify`, { code, newPassword }).then(() => ({ success: true })),
  requestEmailCode: () => post(`${profilePath}/email/mfa/request`, {}),
  verifyEmailCode: (code, newEmail) =>
    api.post(`${profilePath}/email/mfa/verify`, { code, newEmail }).then((r) => profileShape(r.data)),
}

/* ---- reference data loaded from the plant's workbooks ---- */
export const masterData = {
  summary: () => get('/master-data/summary'),
}

/* ---- Live Notifications & Alerts connected directly to Railway DB ---- */
export const notifications = {
  list: (params) =>
    agent
      .get('/api/v1/notifications', { params })
      .then((r) => r.data)
      .catch(() => get('/dashboard/alerts')),
  markRead: (notificationId) =>
    agent
      .post('/api/v1/notifications/mark-read', { notificationId })
      .then((r) => r.data)
      .catch(() => post('/notifications/mark-read', { notificationId })),
  markAllRead: () =>
    agent
      .post('/api/v1/notifications/mark-all-read')
      .then((r) => r.data)
      .catch(() => post('/notifications/mark-all-read', {})),
}

/* ---- Member 3 aggregation view ---- */
export const dashboard = {
  summary: () => get('/dashboard/summary'),
  safetyByZone: () => get('/dashboard/safety-score'),
  alerts: () =>
    agent
      .get('/api/v1/notifications')
      .then((r) => r.data)
      .catch(() => get('/dashboard/alerts')),
  monthlyTrend: () => get('/dashboard/monthly-trend'),
  pyramid: () => get('/dashboard/pyramid'),
}

/* ---- Member 1: incidents, permits, JSA, risk ---- */
export const incidents = {
  list: (params) => get('/incidents', params),
  byId: (id) => get(`/incidents/${id}`),
  create: (body) => post('/incidents', body),
  stats: () => get('/incidents/stats'),
  rootCauses: () => get('/incidents/root-causes'),
  rca: (id) => get(`/incidents/${id}/rca`),
}

export const capa = {
  list: (params) => get('/capa', params),
}

export const permits = {
  list: (params) => get('/permits', params),
  byId: (id) => get(`/permits/${id}`),
  create: (body) => post('/permits', body),
  stats: () => get('/permits/stats'),
  approvals: (id) => get(`/permits/${id}/approvals`),
  approve: (id, note) => post(`/permits/${id}/approve`, { note }),
  suspend: (id, reason) => post(`/permits/${id}/suspend`, { reason }),
  close: (id, note) => post(`/permits/${id}/close`, { note }),
  simops: () => get('/permits/simops'),
  checklist: (type) => get('/permits/checklist', { type }),
}

export const risk = {
  register: (params) => get('/risk/hazards', params),
  distribution: () => get('/risk/distribution'),
}

export const jsa = {
  list: () => get('/jsa'),
  byId: (id) => get(`/jsa/${id}`),
  stats: () => get('/jsa/stats'),
}

/* ---- Member 2: operations ---- */
export const departments = {
  list: () => get('/departments'),
}

export const inspections = {
  schedule: () => get('/inspections/schedule'),
  findings: (params) => get('/inspections/findings', params),
  stats: () => get('/inspections/stats'),
  templates: () => get('/inspections/templates'),
  createSchedule: (body) => post('/inspections/schedule', body),
  submitWalk: (body) => post('/inspections/walk', body),
  updateFindingStatus: (id, body) => post(`/inspections/findings/${id}/status`, body),
}

export const training = {
  programs: () => get('/training/programs'),
  expiring: () => get('/training/expiring'),
  stats: () => get('/training/stats'),
  schedule: () => get('/training/schedule'),
  register: (body) => post('/training/register', body),
}

export const hazmat = {
  list: () => get('/hazmat/chemicals'),
  stats: () => get('/hazmat/stats'),
  compatibility: () => get('/hazmat/compatibility'),
}

export const health = {
  exams: () => get('/occupational-health/exams'),
  stats: () => get('/occupational-health/stats'),
  exposure: () => get('/occupational-health/exposure'),
  schedule: () => get('/occupational-health/schedule'),
  registerExam: (body) => post('/occupational-health/exams', body),
}

export const reports = {
  kpis: () => get('/reports/kpis'),
  trirTrend: () => get('/reports/trir-trend'),
  iso45001: () => get('/reports/iso45001'),
  heatmap: () => get('/reports/heatmap'),
  leading: () => get('/reports/leading-indicators'),
  sendManagement: (body) => post('/reports/send-management', body),
}

export const integrations = {
  list: () => get('/integrations'),
}

export const security = {
  auditLog: (params) => get('/audit-log', params),
  roles: () => get('/security/roles'),
  sessions: () => get('/security/sessions'),
}

/* ---- Member 6: PPE & fire equipment ---- */
export const fire = {
  list: (params) => get('/fire-equipment', params),
  byId: (id) => get(`/fire-equipment/${id}`),
  create: (body) => post('/fire-equipment', body),
  update: (id, body) => api.put(`/fire-equipment/${id}`, body).then((r) => r.data),
  delete: (id) => api.delete(`/fire-equipment/${id}`).then((r) => r.data),
  stats: () => get('/fire-equipment/stats'),
  attention: () => get('/fire-equipment/attention'),
  coverage: () => get('/fire-equipment/coverage'),
  inspections: (params) => get('/fire/inspections', params),
  createInspection: (body) => post('/fire/inspections', body),
  service: (id, body) => post(`/fire-equipment/${id}/service`, body),
}

export const ppe = {
  stock: (params) => get('/ppe/items', params),
  items: (params) => get('/ppe/items', params),
  belowThreshold: () => get('/ppe/items/below-threshold'),
  byId: (id) => get(`/ppe/items/${id}`),
  create: (body) => post('/ppe/items', body),
  update: (id, body) => api.put(`/ppe/items/${id}`, body).then((r) => r.data),
  delete: (id) => api.delete(`/ppe/items/${id}`).then((r) => r.data),
  summary: () => get('/ppe/items/summary'),
  daysUntilStockout: (id) => get(`/ppe/items/${id}/days-until-stockout`),

  transactions: () => get('/ppe/transactions'),
  createTransaction: (body) => post('/ppe/transactions', body),
  deleteTransaction: (id) => api.delete(`/ppe/transactions/${id}`).then((r) => r.data),
  transactionsSummary: () => get('/ppe/transactions/summary'),

  matrix: () => get('/ppe/matrix'),
  matrixSummary: () => get('/ppe/matrix/summary'),
  createMatrixRule: (body) => post('/ppe/matrix', body),
  deleteMatrixRule: (id) => api.delete(`/ppe/matrix/${id}`).then((r) => r.data),

  fixedAssets: () => get('/ppe/fixed-assets'),
  createFixedAsset: (body) => post('/ppe/fixed-assets', body),
  deleteFixedAsset: (id) => api.delete(`/ppe/fixed-assets/${id}`).then((r) => r.data),
}

/* ---- AI students: simulation feed + conversational endpoint ---- */
export const iot = {
  sensors: () => get('/iot/sensors'),
  events: (params) => get('/iot/events', params),
  detections: () => get('/ai/detections'),
  models: () => get('/ai/models'),
  wearables: () => get('/iot/wearables'),
}

export const assistant = {
  /** Conversational RAG & CRUD endpoint on the FastAPI service with RBAC enforcement. */
  ask: (question, history, model_mode = 'auto', user_role = 'HSE_MANAGER', admin_user_id = 'USR-DEV') =>
    agent.post('/ask', { question, history, model_mode, user_role, admin_user_id }).then((r) => r.data),
  suggestions: () => agent.get('/suggestions').then((r) => r.data),
}
