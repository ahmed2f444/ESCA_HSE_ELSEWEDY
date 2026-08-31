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
const put = (url, body) => api.put(url, body).then((r) => r.data)
const del = (url) => api.delete(url).then((r) => r.data)

export const auth = {
  login: (username, password) => post('/auth/login', { username, password }),
  me: () => get('/auth/me'),
}

export function resolveAvatarUrl(path) {
  if (!path || typeof path !== 'string') return null
  const trimmed = path.trim()
  if (!trimmed) return null
  if (trimmed.startsWith('data:') || trimmed.startsWith('blob:') || trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed
  }
  const apiBase = import.meta.env.VITE_API_BASE_URL || ''
  if (apiBase && apiBase.startsWith('http')) {
    try {
      const url = new URL(apiBase)
      return `${url.origin}${trimmed.startsWith('/') ? '' : '/'}${trimmed}`
    } catch {}
  }
  return trimmed.startsWith('/') ? trimmed : `/${trimmed}`
}

const profilePath = '/users/me'
const profileShape = (data) => {
  const localAvatar = (() => {
    try {
      const u = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
      return u.avatarPath || localStorage.getItem('esca.hse.avatar') || null
    } catch {
      return null
    }
  })()
  const rawAvatar = data.avatarPath || data.avatar_path || localAvatar
  return {
    user_id: data.userId || data.user_id,
    username: data.username,
    full_name: data.fullName || data.full_name || '',
    email: data.email || '',
    phone: data.phone || '',
    job_title: data.jobTitle || data.job_title || '',
    avatar_path: resolveAvatarUrl(rawAvatar),
    zone_name: data.zoneName || data.zone_name || '',
    department_name: data.departmentName || data.department_name || '',
  }
}

export function getLocalFallbackProfile() {
  const fallbackAvatar = (() => {
    try {
      const u = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
      return u.avatarPath || localStorage.getItem('esca.hse.avatar') || null
    } catch {
      return null
    }
  })()

  try {
    const raw = localStorage.getItem('esca.hse.user')
    if (raw) {
      const u = JSON.parse(raw)
      return profileShape({
        userId: u.id || u.user_id || 1,
        employeeId: u.employeeId || 'EMP-001',
        username: u.username || 'mostafa',
        fullName: u.displayName || u.name || u.fullName || 'مصطفى محمد',
        email: u.email || 'mostafa@elsewedy.com',
        phone: u.phone || '01000000001',
        jobTitle: u.roleLabel || u.jobTitle || u.job_title || u.roleAr || 'مدير السلامة والصحة المهنية (HSE Manager)',
        zoneName: u.zone || u.zoneName || u.zone_name || 'خطوط العزل CCV',
        departmentName: u.department || u.departmentName || u.department_name || 'قطاع الإنتاج والتصنيع (ESCA)',
        avatarPath: u.avatarPath || fallbackAvatar,
      })
    }
  } catch {}
  return profileShape({
    userId: 1,
    employeeId: 'EMP-001',
    username: 'mostafa',
    fullName: 'مصطفى محمد',
    email: 'mostafa@elsewedy.com',
    phone: '01000000001',
    jobTitle: 'مدير السلامة والصحة المهنية (HSE Manager)',
    zoneName: 'خطوط العزل CCV',
    departmentName: 'قطاع الإنتاج والتصنيع (ESCA)',
    avatarPath: fallbackAvatar,
  })
}

export const profile = {
  get: () =>
    get(profilePath)
      .then((data) => {
        const shape = profileShape(data)
        const local = getLocalFallbackProfile()
        if (!shape.avatar_path && local.avatar_path) {
          shape.avatar_path = local.avatar_path
        }
        return shape
      })
      .catch((err) => {
        console.warn('Profile API get failed, using local session profile:', err)
        return getLocalFallbackProfile()
      }),
  update: (fields) =>
    api.patch(profilePath, {
      fullName: fields.full_name,
      username: fields.username,
    })
      .then((r) => {
        if (r.data?.token) {
          tokenStore.set(r.data.token)
        }
        const shape = profileShape(r.data)
        try {
          const raw = localStorage.getItem('esca.hse.user')
          const u = raw ? JSON.parse(raw) : {}
          u.displayName = shape.full_name || u.displayName
          u.name = shape.full_name || u.name
          u.username = shape.username || u.username
          u.email = shape.email || u.email
          u.phone = shape.phone || u.phone
          u.roleLabel = shape.job_title || u.roleLabel
          u.zone = shape.zone_name || u.zone
          u.department = shape.department_name || u.department
          if (shape.avatar_path) u.avatarPath = shape.avatar_path
          localStorage.setItem('esca.hse.user', JSON.stringify(u))
          window.dispatchEvent(new CustomEvent('hse:user-updated', { detail: u }))
        } catch {}
        return shape
      })
      .catch((err) => {
        console.warn('Profile API patch failed, updating local state:', err)
        const current = getLocalFallbackProfile()
        const updated = {
          ...current,
          full_name: fields.full_name !== undefined ? fields.full_name : current.full_name,
          username: fields.username !== undefined ? fields.username : current.username,
          phone: fields.phone !== undefined ? fields.phone : current.phone,
          job_title: fields.job_title !== undefined ? fields.job_title : current.job_title,
          zone_name: fields.zone_name !== undefined ? fields.zone_name : current.zone_name,
          department_name: fields.department_name !== undefined ? fields.department_name : current.department_name,
          email: fields.email !== undefined ? fields.email : current.email,
        }
        try {
          const raw = localStorage.getItem('esca.hse.user')
          const u = raw ? JSON.parse(raw) : {}
          u.displayName = updated.full_name
          u.name = updated.full_name
          u.username = updated.username
          u.email = updated.email
          u.phone = updated.phone
          u.roleLabel = updated.job_title
          u.zone = updated.zone_name
          u.department = updated.department_name
          localStorage.setItem('esca.hse.user', JSON.stringify(u))
          window.dispatchEvent(new CustomEvent('hse:user-updated', { detail: u }))
        } catch {}
        return updated
      }),
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
  update: (id, body) => put(`/permits/${id}`, body),
  delete: (id, reason) => del(`/permits/${id}${reason ? `?reason=${encodeURIComponent(reason)}` : ''}`),
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
  create: (body) => post('/risk/hazards', body),
}

export const jsa = {
  list: (params) => get('/jsa', params),
  byId: (id) => get(`/jsa/${id}`),
  stats: () => get('/jsa/stats'),
  create: (body) => post('/jsa', body),
  update: (id, body) => api.put(`/jsa/${id}`, body).then((r) => r.data),
  patch: (id, body) => api.patch(`/jsa/${id}`, body).then((r) => r.data),
  approve: (id) => api.patch(`/jsa/${id}/approve`, {}).then((r) => r.data),
  delete: (id) => api.delete(`/jsa/${id}`).then((r) => r.data),
  addStep: (id, body) => post(`/jsa/${id}/steps`, body),
  deleteStep: (id, stepId) => api.delete(`/jsa/${id}/steps/${stepId}`).then((r) => r.data),
  linkPermit: (id, permitId) => post(`/jsa/${id}/link-permit`, { permitId }),
  unlinkPermit: (id, permitId) => post(`/jsa/${id}/unlink-permit`, { permitId }),
  availablePermits: () => get('/jsa/available-permits'),
}

/* ---- Member 2: operations ---- */
export const departments = {
  list: () => get('/departments'),
  rawList: () => get('/v1/organization/departments'),
  createZone: (body) => post('/v1/organization/zones', body),
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
  list: (params) =>
    agent
      .get('/api/v1/hazmat/chemicals', { params })
      .then((r) => r.data)
      .catch(() => get('/hazmat/chemicals', params)),
  byId: (id) =>
    agent
      .get(`/api/v1/hazmat/chemicals/${id}`)
      .then((r) => r.data)
      .catch(() => get(`/hazmat/chemicals/${id}`)),
  create: (body) =>
    agent
      .post('/api/v1/hazmat/chemicals', body)
      .then((r) => r.data)
      .catch(() => post('/hazmat/chemicals', body)),
  update: (id, body) =>
    agent
      .put(`/api/v1/hazmat/chemicals/${id}`, body)
      .then((r) => r.data)
      .catch(() => api.put(`/hazmat/chemicals/${id}`, body).then((r) => r.data)),
  delete: (id) =>
    agent
      .delete(`/api/v1/hazmat/chemicals/${id}`)
      .then((r) => r.data)
      .catch(() => api.delete(`/hazmat/chemicals/${id}`).then((r) => r.data)),
  stats: () =>
    agent
      .get('/api/v1/hazmat/stats')
      .then((r) => r.data)
      .catch(() => get('/hazmat/stats')),
  compatibility: () => get('/hazmat/compatibility'),
  sdsList: (params) => get('/hazmat/sds', params),
  createSds: (body) => post('/hazmat/sds', body),
  updateSds: (id, body) => api.put(`/hazmat/sds/${id}`, body).then((r) => r.data),
  deleteSds: (id) => api.delete(`/hazmat/sds/${id}`).then((r) => r.data),
}

export const health = {
  exams: () => get('/occupational-health/exams'),
  stats: () => get('/occupational-health/stats'),
  exposure: () => get('/occupational-health/exposure'),
  schedule: () => get('/occupational-health/schedule'),
  registerExam: (body) => post('/occupational-health/exams', body),

  // ── Full CRUD via OccupationalHealthController (mirrors Certificates pattern) ──
  records: (params) => get('/occupational-health/records', params),
  recordById: (id) => get(`/occupational-health/records/${id}`),
  createRecord: (body) => post('/occupational-health/records', body),
  updateRecord: (id, body) => api.patch(`/occupational-health/records/${id}`, body).then((r) => r.data),
  replaceRecord: (id, body) => api.put(`/occupational-health/records/${id}`, body).then((r) => r.data),
  deleteRecord: (id) => api.delete(`/occupational-health/records/${id}`).then((r) => r.data),
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
  sync: () => post('/integrations/sync'),
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
  /** Conversational RAG & CRUD endpoint on the FastAPI service with RBAC enforcement and resilient offline fallback. */
  ask: async (question, history, model_mode = 'auto', user_role = 'HSE_MANAGER', admin_user_id = 'USR-DEV') => {
    try {
      const res = await agent.post('/ask', { question, history, model_mode, user_role, admin_user_id })
      return res.data
    } catch (err) {
      console.warn('[Assistant] Live agent service unreachable, utilizing local assistant engine fallback:', err)
      const { answer: mockAnswer } = await import('./mock/agent.js')
      const fallback = mockAnswer(question)
      return {
        session_id: 'fallback-' + Date.now(),
        answer: fallback.answer,
        tool_calls: (fallback.tools || []).map((t) => ({
          tool_name: t.name,
          query_summary: `${t.name} (${t.rowCount || 0} records)`,
          rows_returned: t.rowCount || 0,
        })),
        tools: fallback.tools || [],
        model_used: 'ESCA Intelligent Assistant (Local Engine / Offline Mode)',
      }
    }
  },
  suggestions: () =>
    agent
      .get('/suggestions')
      .then((r) => r.data)
      .catch(() => [
        'ما هي الحوادث المفتوحة حالياً وما درجة خطورتها؟',
        'اعرض تصاريح العمل النشطة والمنتهية في الموقع ePTW',
        'افحص تعارضات العمليات المتزامنة SIMOPS في منطقة الإنتاج',
        'ما هي إحصائيات ونسبة الامتثال لجولات التفتيش والسلامة؟',
        'ما هي مطافئ الحريق التي تحتاج فحص دوري أو إعادة تعبئة؟',
        'صرف مهمة وقاية شخصية (PPE) للموظف وتحديث المخزون',
        'اعرض أحدث تنبيهات حساسات الغازات والحرارة الذكية IoT',
        'احسب مؤشرات TRIR و LTIFR لشهر يوليو 2026',
        'ما هي القواعد الذهبية للسلامة (ESCA Golden Rules)؟',
      ]),

  /**
   * High-accuracy multilingual speech transcription via Whisper Large v3.
   * Handles Egyptian Arabic (ar-EG), Gulf/MSA (ar-SA), English (en-US), and mixed language queries.
   */
  transcribe: async (audioBlob, language = 'auto') => {
    const formData = new FormData()
    const ext = audioBlob.type?.includes('ogg') ? 'ogg' : audioBlob.type?.includes('mp4') ? 'm4a' : 'webm'
    formData.append('file', audioBlob, `voice_input.${ext}`)
    if (language && language !== 'auto' && language !== 'multilingual' && language !== 'mixed') {
      formData.append('language', language)
    }
    const res = await agent.post('/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 35000,
    })
    return res.data
  },
}


