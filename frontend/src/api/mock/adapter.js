import * as db from './data.js'
import { readSensors, pushEvent, recentEvents } from './live.js'
import { answer } from './agent.js'

/**
 * Local axios adapter used while the Spring Boot / FastAPI services are still
 * being built. It matches the same paths the real services will expose, so
 * switching to them is a single env flag — no call sites change.
 *
 * Deliberately imperfect: it adds latency and can fail, because a UI that has
 * only ever seen instant success hides its own loading and error states.
 */

const delay = (ms) => new Promise((r) => setTimeout(r, ms))

const ok = (data, config) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: { 'content-type': 'application/json' },
  config,
  request: {},
})

function fail(status, message, config) {
  const err = new Error(message)
  err.config = config
  err.response = { status, data: { message }, config, headers: {} }
  return err
}

/* ---------------- route table ---------------- */
/* [method, path pattern, handler(params, query, body)] */

const routes = [
  ['post', '/auth/login', (_p, _q, body) => {
    // Usernames are case-insensitive and whitespace-tolerant: phone keyboards
    // auto-capitalise the first letter and a trailing space survives a paste,
    // and neither should read as a wrong password. The password itself is
    // compared exactly, minus surrounding whitespace.
    const username = String(body?.username ?? '').trim().toLowerCase()
    const password = String(body?.password ?? '').trim()

    const u = db.users.find((x) => x.username === username && x.password === password)
    // One message for both cases on purpose — telling the caller which half was
    // wrong hands an attacker a list of valid usernames.
    if (!u) throw fail(401, 'اسم المستخدم أو كلمة المرور غير صحيحة')

    // A correct password on a suspended account is still a refused login. The
    // sheets mark both the account and its role assignment, and either one
    // being non-active is enough to keep the holder out.
    if (u.status !== 'ACTIVE' || (u.assignmentStatus && u.assignmentStatus !== 'ACTIVE')) {
      throw fail(403, 'الحساب موقوف — كلّم إدارة السلامة والصحة المهنية')
    }
    const { password: _stored, ...safe } = u
    // Shaped like a JWT so the console (and the Authorization header) behave the same.
    const payload = btoa(JSON.stringify({ sub: u.username, role: u.role, exp: Date.now() + 288e5 }))
    return { token: `mock.${payload}.sig`, user: safe }
  }],
  ['get', '/auth/me', () => {
    const raw = localStorage.getItem('esca.hse.user')
    if (!raw) throw fail(401, 'الجلسة غير صالحة')
    return JSON.parse(raw)
  }],

  /* master data — the reference-data coverage sheet */
  ['get', '/master-data/summary', () => ({
    ...db.masterSummary,
    sheets: db.sheetMeta,
    departments: db.departments.flatMap((s) => s.zones),
    zoneCount: db.departments.reduce((n, s) => n + s.zones.reduce((m, z) => m + z.zoneCount, 0), 0),
  })],

  /* dashboard */
  ['get', '/dashboard/summary', () => db.dashboardSummary],
  ['get', '/dashboard/safety-score', () => db.safetyByZone],
  ['get', '/dashboard/alerts', () => db.dashboardAlerts],
  ['get', '/dashboard/monthly-trend', () => db.monthlyTrend],
  ['get', '/dashboard/pyramid', () => db.pyramid],

  /* incidents */
  ['get', '/incidents/stats', () => db.incidentStats],
  ['get', '/incidents/root-causes', () => db.rootCauses],
  ['get', '/incidents/:id/rca', (p) => db.rcaByIncident[p.id] || null],
  ['get', '/incidents/:id', (p) => {
    const found = db.incidents.find((i) => i.id === p.id)
    if (!found) throw fail(404, `لا يوجد بلاغ بالرقم ${p.id}`)
    return found
  }],
  ['get', '/incidents', (_p, q) => {
    // Newest first — a freshly reported incident must land at the top of the register.
    let rows = [...created.incidents, ...db.incidents]
    if (q.status && q.status !== 'all') {
      const open = ['مفتوح', 'تحت التحقيق', 'إجراء تصحيحي']
      rows = rows.filter((r) =>
        q.status === 'open' ? open.includes(r.status)
          : q.status === 'investigating' ? r.status === 'تحت التحقيق'
          : r.status === 'مغلق'
      )
    }
    if (q.q) {
      const t = q.q.trim()
      rows = rows.filter((r) => [r.id, r.zone, r.type, r.description, r.injured, r.owner].join(' ').includes(t))
    }
    return rows
  }],
  ['post', '/incidents', (_p, _q, body) => {
    const seq = 90 + created.incidents.length
    const rec = {
      id: `INC-2026-00${seq}`,
      date: (body.occurredAt || '').slice(0, 10) || '2026-08-06',
      time: (body.occurredAt || '').slice(11, 16) || '—',
      zone: body.zone,
      type: body.type,
      classification: 'Reported',
      description: body.description,
      severity: body.severity,
      severityTone: { منخفضة: 'nu', متوسطة: 'wn', عالية: 'cr', حرجة: 'cr' }[body.severity] || 'nu',
      injured: body.injured || '—',
      employeeNo: body.employeeNo || '—',
      status: 'مفتوح',
      statusTone: 'wn',
      owner: body.owner,
      lostDays: 0,
      immediateAction: body.immediateAction || '—',
      dueDate: body.dueDate || '—',
      linkedPermit: null,
      linkedHazard: null,
    }
    created.incidents.unshift(rec)
    pushEvent({ code: 'INCIDENT_REPORTED', tone: 'cr', source: rec.id, detail: rec.zone, action: 'إخطار HSE Manager' })
    return rec
  }],
  ['get', '/capa', () => db.capa],

  /* permits */
  ['get', '/permits/stats', () => db.permitStats],
  ['get', '/permits/simops', () => db.simops],
  ['get', '/permits/checklist', (_p, q) => db.permitChecklists[q.type] || []],
  ['get', '/permits/:id/approvals', (p) => {
    const steps = db.permitApprovalsByPermit[p.id] || []
    const signed = steps.filter((s) => s.signature).pop()
    return {
      steps,
      signature: signed
        ? { name: signed.approver, algo: 'SHA-256', timestamp: signed.decidedAt, hash: signed.signature }
        : null,
      approved: approvedPermits.has(p.id) || steps.every((s) => s.state === 'done'),
    }
  }],
  ['post', '/permits/:id/approve', (p) => {
    approvedPermits.add(p.id)
    return { id: p.id, status: 'نشط', approvedBy: 'رافع صابر', at: new Date().toISOString() }
  }],
  ['get', '/permits/:id', (p) => {
    const found = db.permits.find((x) => x.id === p.id)
    if (!found) throw fail(404, `لا يوجد تصريح بالرقم ${p.id}`)
    return found
  }],
  ['get', '/permits', (_p, q) => {
    let rows = (db.permits || []).map((r) => (approvedPermits.has(r.id) ? { ...r, rawStatus: 'ACTIVE', status: 'نشط', statusTone: 'safe' } : r))
    if (q && q.type && q.type !== 'all') rows = rows.filter((r) => r.type === q.type)
    return rows
  }],
  ['post', '/permits', (_p, _q, body) => {
    const newId = 'PTW-' + String((db.permits?.length || 0) + 1).padStart(3, '0')
    const item = {
      id: newId,
      type: body.type || 'HOT_WORK',
      typeLabel: body.type === 'HOT_WORK' ? 'عمل ساخن' : 'تصريح عمل',
      description: body.description || 'أعمال صيانة',
      zone: body.zone || 'خطوط العزل CCV',
      from: body.from || '08:00',
      to: body.to || '16:00',
      date: body.date || new Date().toISOString().slice(0, 10),
      requester: body.requester || 'م. مصطفى (مدير السلامة)',
      issuer: body.issuer || 'م. مصطفى (مدير السلامة)',
      executor: body.executor || 'فريق الصيانة الداخلي',
      jsa: body.jsa || 'JSA-001',
      risk: body.riskLevel || 'HIGH',
      riskLevel: body.riskLevel || 'HIGH',
      riskLabel: body.riskLevel || 'عالي (High)',
      rawStatus: 'PENDING_APPROVAL',
      status: 'بانتظار الموافقة',
      statusTone: 'in',
      flag: 'OK',
    }
    db.permits = [item, ...(db.permits || [])]
    return item
  }],
  ['post', '/permits/:id/suspend', (p) => {
    if (db.permits) {
      db.permits = db.permits.map((x) => (x.id === p.id ? { ...x, rawStatus: 'SUSPENDED', status: 'موقوف', statusTone: 'cr' } : x))
    }
    return { success: true, id: p.id, status: 'SUSPENDED' }
  }],
  ['post', '/permits/:id/close', (p) => {
    if (db.permits) {
      db.permits = db.permits.map((x) => (x.id === p.id ? { ...x, rawStatus: 'CLOSED', status: 'مغلق', statusTone: 'wn' } : x))
    }
    return { success: true, id: p.id, status: 'CLOSED' }
  }],

  /* risk / JSA */
  ['get', '/risk/hazards', (_p, q) => {
    let rows = db.hazards
    if (q.cell) {
      const [prob, sev] = q.cell.split('x').map(Number)
      rows = rows.filter((h) => h.probability === prob && h.severity === sev)
    }
    return rows
  }],
  ['get', '/risk/distribution', () => ({ bands: db.riskDistribution, summary: db.riskSummary })],
  ['get', '/jsa/stats', () => db.jsaStats],
  ['get', '/jsa/:id', (p) => db.jsaDetail[p.id] || null],
  ['get', '/jsa', () => db.jsaList],

  /* operations */
  ['get', '/departments', () => db.departments],
  ['get', '/inspections/schedule', () => db.inspectionSchedule],
  ['post', '/inspections/schedule', (_p, _q, body) => {
    const item = {
      type: body.type || 'تفتيش السلامة العام',
      zone: body.zone || 'خطوط العزل CCV',
      frequency: body.frequency || 'أسبوعي',
      owner: body.owner || 'م. مصطفى (مدير السلامة)',
      next: body.next || new Date().toISOString().slice(0, 10),
      status: 'مجدول',
      tone: 'in',
      score: null,
    }
    db.inspectionSchedule = [item, ...(db.inspectionSchedule || [])]
    return item
  }],
  ['get', '/inspections/findings', () => db.inspectionFindings],
  ['get', '/inspections/stats', () => ({ ...db.inspectionStats, field: db.fieldInspector })],
  ['get', '/inspections/templates', () => db.inspectionTemplates],
  ['post', '/inspections/walk', (_p, _q, body) => {
    const item = {
      type: body.type || 'تفتيش ميداني دوري',
      zone: body.zone || 'خطوط العزل CCV',
      frequency: 'أسبوعي',
      owner: body.inspector || 'م. مصطفى (مدير السلامة)',
      next: new Date().toISOString().slice(0, 10),
      status: 'مكتمل',
      tone: 'ok',
      score: body.score || 95,
    }
    db.inspectionSchedule = [item, ...(db.inspectionSchedule || [])]
    if (body.findings && body.findings.length > 0) {
      db.inspectionFindings = [...body.findings, ...(db.inspectionFindings || [])]
    }
    return { success: true, item }
  }],
  ['post', '/inspections/findings/:id/status', (p, _q, body) => {
    const fid = parseInt(p.id, 10)
    const state = body.state || body.status || 'مغلق'
    if (db.inspectionFindings) {
      db.inspectionFindings = db.inspectionFindings.map((f) =>
        f.id === fid ? { ...f, state } : f
      )
    }
    return { success: true, id: fid, state }
  }],
  ['get', '/training/programs', () => db.trainingPrograms],
  ['get', '/training/expiring', () => db.trainingExpiring],
  ['get', '/training/stats', () => db.trainingStats],
  ['get', '/training/schedule', () => {
    return (db.trainingSchedule || [
      { id: 'TRN-001', certId: 1, employee: 'محمود عبد الله', dept: 'خط الإنتاج A', course: 'السلامة العامة (General Induction)', provider: 'ESCA HSE Academy', issueDate: '2025-01-15', expiryDate: '2026-12-15', evidenceRef: 'CERT-2026-0001', status: 'سارية ومعتمدة', statusTone: 'ok' },
      { id: 'TRN-002', certId: 2, employee: 'هبة فؤاد', dept: 'خط الإنتاج B', course: 'العمل الساخن (Hot Work)', provider: 'Elsewedy Technical Training Center', issueDate: '2025-03-01', expiryDate: '2027-01-04', evidenceRef: 'CERT-2026-0002', status: 'سارية ومعتمدة', statusTone: 'ok' },
      { id: 'TRN-003', certId: 3, employee: 'أحمد سامي', dept: 'ورشة الصيانة الميكانيكية', course: 'القفل وتطبيق بطاقة LOTO', provider: 'External Certified Provider', issueDate: '2025-04-15', expiryDate: '2027-01-24', evidenceRef: 'CERT-2026-0003', status: 'سارية ومعتمدة', statusTone: 'ok' },
      { id: 'TRN-004', certId: 4, employee: 'كريم رشاد', dept: 'المخازن والخام', course: 'العمل على ارتفاع (Working at Height)', provider: 'ESCA HSE Academy', issueDate: '2025-05-30', expiryDate: '2027-02-13', evidenceRef: 'CERT-2026-0004', status: 'مجدولة للتجديد', statusTone: 'wn' },
    ])
  }],
  ['post', '/training/register', (_p, _q, body) => {
    const newId = 'TRN-' + String((db.trainingSchedule?.length || 4) + 1).padStart(3, '0')
    const item = {
      id: newId,
      certId: (db.trainingSchedule?.length || 4) + 1,
      employee: body.employeeName || 'محمود عبد الله',
      dept: body.dept || 'قطاع الإنتاج والتصنيع',
      course: body.courseName || 'السلامة العامة',
      provider: body.provider || 'ESCA HSE Academy',
      issueDate: body.issueDate || new Date().toISOString().slice(0, 10),
      expiryDate: body.expiryDate || new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10),
      evidenceRef: body.evidenceRef || ('CERT-' + Math.floor(Math.random() * 9000 + 1000)),
      status: 'سارية ومعتمدة',
      statusTone: 'ok',
    }
    if (!db.trainingSchedule) db.trainingSchedule = []
    db.trainingSchedule = [item, ...db.trainingSchedule]
    return item
  }],
  ['get', '/hazmat/chemicals', () => db.chemicals],
  ['get', '/hazmat/stats', () => db.hazmatStats],
  ['get', '/hazmat/compatibility', () => db.compatibility],
  ['get', '/occupational-health/exams', () => db.healthExams],
  ['get', '/occupational-health/stats', () => db.healthStats],
  ['get', '/occupational-health/exposure', () => db.exposureMonitoring],
  ['get', '/occupational-health/schedule', () => {
    return (db.healthSchedule || [
      { id: 'HEX-001', employee: 'محمود عبد الله', protocol: 'فحص قياس السمع (Audiometry)', scheduledDate: '2026-08-28', completedDate: '2026-08-28', fitness: 'لائق طبياً', fitnessTone: 'ok', restrictions: 'لا توجد قيود', doctor: 'د. حازم القاضي', nextDueDate: '2027-02-28', status: 'مكتمل', statusTone: 'ok' },
      { id: 'HEX-002', employee: 'هبة فؤاد', protocol: 'فحص وظائف التنفس والرئة (Spirometry)', scheduledDate: '2026-08-29', completedDate: null, fitness: 'قيد الانتظار', fitnessTone: 'wn', restrictions: 'تحت التقييم', doctor: 'د. سمر الشافعي', nextDueDate: '2027-02-28', status: 'مجدول', statusTone: 'in' },
      { id: 'HEX-003', employee: 'أحمد سامي', protocol: 'لياقة الارتفاعات والأماكن المغلقة', scheduledDate: '2026-08-30', completedDate: '2026-08-30', fitness: 'لائق مع قيود', fitnessTone: 'wn', restrictions: 'تجنب العمل على ارتفاعات > 10م', doctor: 'د. حازم القاضي', nextDueDate: '2026-11-30', status: 'مكتمل', statusTone: 'ok' },
    ])
  }],
  ['post', '/occupational-health/exams', (_p, _q, body) => {
    const newId = 'HEX-' + String((db.healthSchedule?.length || 3) + 1).padStart(3, '0')
    const item = {
      id: newId,
      employee: body.employeeName || 'محمود عبد الله',
      protocol: body.protocolName || 'فحص قياس السمع (Audiometry)',
      scheduledDate: body.scheduledDate || new Date().toISOString().slice(0, 10),
      completedDate: body.scheduledDate || new Date().toISOString().slice(0, 10),
      fitness: body.fitnessResultId === 2 ? 'لائق مع قيود' : body.fitnessResultId === 3 ? 'غير لائق مؤقتاً' : 'لائق طبياً',
      fitnessTone: body.fitnessResultId === 2 ? 'wn' : body.fitnessResultId === 3 ? 'cr' : 'ok',
      restrictions: body.restrictions || 'لا توجد قيود',
      doctor: body.doctor || 'د. حازم القاضي',
      nextDueDate: body.nextDueDate || '2027-02-28',
      status: 'مكتمل',
      statusTone: 'ok',
    }
    if (!db.healthSchedule) db.healthSchedule = []
    db.healthSchedule = [item, ...db.healthSchedule]
    return item
  }],

  /* reports */
  ['get', '/reports/kpis', () => db.reportKpis],
  ['get', '/reports/trir-trend', () => db.trirTrend],
  ['get', '/reports/iso45001', () => db.iso45001],
  ['get', '/reports/heatmap', () => db.heatmap],
  ['get', '/reports/leading-indicators', () => db.leadingIndicators],

  /* member 6 */
  ['get', '/fire-equipment/attention', () => db.fireAttention],
  ['get', '/fire-equipment/coverage', () => db.fireCoverage],
  ['get', '/fire-equipment/stats', () => db.fireStats],
  ['get', '/fire-equipment/:id', (p) => (db.fireUnits || []).find((u) => u.equipmentId === p.id || u.code === p.id) || db.fireUnits?.[0]],
  ['post', '/fire-equipment', (_p, _q, body) => ({ success: true, ...body })],
  ['put', '/fire-equipment/:id', (p, _q, body) => ({ success: true, equipmentId: p.id, ...body })],
  ['delete', '/fire-equipment/:id', (p) => ({ success: true, deleted: p.id })],
  ['get', '/fire-equipment', () => db.fireUnits],
  ['get', '/fire/inspections', () => db.fireInspections || []],
  ['post', '/fire/inspections', (_p, _q, body) => ({ success: true, ...body })],

  ['get', '/ppe/stock', () => db.ppeStock],
  ['get', '/ppe/items/below-threshold', () => (db.ppeStock || []).filter((i) => (i.balanceQty ?? i.balance) < (i.reorderThreshold ?? i.threshold))],
  ['get', '/ppe/items/summary', () => ({ totalItems: 10, belowThreshold: 2, lowStock: 1, available: 7 })],
  ['get', '/ppe/items/:id', (p) => (db.ppeStock || []).find((i) => i.ppeItemId === p.id || i.code === p.id) || db.ppeStock?.[0]],
  ['post', '/ppe/items', (_p, _q, body) => ({ success: true, ...body })],
  ['put', '/ppe/items/:id', (p, _q, body) => ({ success: true, ppeItemId: p.id, ...body })],
  ['delete', '/ppe/items/:id', (p) => ({ success: true, deleted: p.id })],
  ['get', '/ppe/items', () => db.ppeStock],
  ['get', '/ppe/transactions', () => db.ppeTransactions || []],
  ['post', '/ppe/transactions', (_p, _q, body) => ({ success: true, ...body })],
  ['delete', '/ppe/transactions/:id', (p) => ({ success: true, deleted: p.id })],
  ['get', '/ppe/fixed-assets', () => db.fixedAssets],
  ['get', '/ppe/matrix', () => db.ppeMatrix],

  /* platform */
  ['get', '/integrations', () => db.integrationList],
  ['get', '/audit-log', (_p, q) => (q.q ? db.auditLog.filter((r) => JSON.stringify(r).includes(q.q)) : db.auditLog)],
  ['get', '/security/roles', () => db.roles],
  ['get', '/security/sessions', () => db.sessions],

  /* AI / IoT simulation */
  ['get', '/iot/sensors', () => readSensors()],
  ['get', '/iot/events', () => recentEvents()],
  ['get', '/iot/wearables', () => db.wearables],
  ['get', '/ai/detections', () => db.detections],
  ['get', '/ai/models', () => ({ models: db.aiModels, stats: db.aiStats })],

  /* agent service (FastAPI) */
  ['post', '/ask', (_p, _q, body) => answer(body?.question || '')],
  ['get', '/suggestions', () => [
    'إيه الحوادث المفتوحة دلوقتي؟',
    'مين الموظفين اللي شهاداتهم منتهية؟',
    'التصاريح اللي هتنتهي خلال ساعتين',
    'أعلى منطقة في عدد الحوادث السنة دي',
    'الطفايات اللي محتاجة استبدال فوري',
  ]],
]

/** Writes made during the session — kept in memory so the demo feels live. */
const created = { incidents: [] }
const approvedPermits = new Set()

function match(pattern, path) {
  const pp = pattern.split('/').filter(Boolean)
  const ap = path.split('/').filter(Boolean)
  if (pp.length !== ap.length) return null
  const params = {}
  for (let i = 0; i < pp.length; i++) {
    if (pp[i].startsWith(':')) params[pp[i].slice(1)] = decodeURIComponent(ap[i])
    else if (pp[i] !== ap[i]) return null
  }
  return params
}

export default async function mockAdapter(config) {
  const method = (config.method || 'get').toLowerCase()

  let url = config.url || ''
  if (config.baseURL && url.startsWith(config.baseURL)) url = url.slice(config.baseURL.length)
  const [rawPath, rawQs] = url.split('?')
  const path = rawPath.replace(/\/+$/, '') || '/'

  const query = { ...Object.fromEntries(new URLSearchParams(rawQs || '')), ...(config.params || {}) }
  let body = config.data
  if (typeof body === 'string') {
    try {
      body = JSON.parse(body)
    } catch {
      body = null
    }
  }

  await delay(90 + Math.random() * 220)

  for (const [m, pattern, handler] of routes) {
    if (m !== method) continue
    const params = match(pattern, path)
    if (!params) continue
    try {
      return ok(handler(params, query, body), config)
    } catch (e) {
      if (e.response) return Promise.reject(e)
      return Promise.reject(fail(500, e.message || 'خطأ داخلي في المحاكاة', config))
    }
  }

  return Promise.reject(fail(404, `المسار غير معرّف في المحاكاة: ${method.toUpperCase()} ${path}`, config))
}
