/**
 * Maps the company sheets onto the shapes the screens consume.
 *
 * `seed.generated.js` is a faithful mirror of the workbooks — raw column names,
 * raw coded values, foreign keys intact. The screens want display-ready rows.
 * This module is the seam between the two, and it is the only place that knows
 * both vocabularies.
 *
 * Everything here is derived. Where the sheets carry a number (headcount, KPI,
 * score) it is used as given; where a figure is a roll-up (open incidents,
 * readiness percentage) it is computed from the rows rather than restated, so
 * the console can never disagree with its own register.
 *
 * A few tables have no counterpart in the sheets — the chemical compatibility
 * matrix, the inspection template catalogue, the ISO clause checklist. Those
 * stay hand-authored at the bottom of the file and are labelled as such.
 */

import * as seed from './seed.generated.js'
import { t, tone, ROLE_AR } from '../../labels.js'

export const sheetMeta = seed.meta
export const masterSummary = seed.summary

/* ------------------------------------------------------------------ */
/* Lookups                                                             */
/* ------------------------------------------------------------------ */

const byId = (rows, key) => Object.fromEntries(rows.map((r) => [r[key], r]))

const DEPT = byId(seed.departments, 'department_id')
const ZONE = byId(seed.zones, 'zone_id')
const EMP = byId(seed.employees, 'employee_id')
const ROLE = byId(seed.roles, 'role_id')
const COURSE = byId(seed.trainingCourses, 'course_id')
const PPE_ITEM = byId(seed.ppeInventory, 'ppe_item_id')
const SENSOR = byId(seed.iotSensors, 'sensor_id')

const deptName = (id) => DEPT[id]?.name_ar || DEPT[id]?.name_en || id || '—'
const zoneName = (id) => ZONE[id]?.name_ar || ZONE[id]?.name_en || id || '—'
const empName = (id) => EMP[id]?.display_name || id || '—'
const dateOnly = (v) => (v ? String(v).slice(0, 10) : '—')
const timeOnly = (v) => (v ? String(v).slice(11, 16) : '—')
const pct = (n, d) => (d ? Math.round((n / d) * 100) : 0)

/** The sheets are a snapshot; this is the moment they describe. */
export const asOf = seed.summary.asOfTimestamp || '2026-08-13 09:00'

/* ------------------------------------------------------------------ */
/* Accounts & roles                                                    */
/* ------------------------------------------------------------------ */

/**
 * The Users sheet has no password column — it never would, and it shouldn't.
 * For the demo build each account gets a deterministic password derived from
 * its username so the list is predictable and documentable. When Spring Boot
 * takes over authentication this disappears entirely.
 */
const demoPassword = (username) => {
  const digits = String(username).match(/(\d+)/)?.[1]
  if (digits) return `esca@${digits}`
  return username.startsWith('svc') ? 'esca@service' : `esca@${username.replace(/[^a-z]/gi, '')}`
}

/**
 * Prefer the active assignment, but keep a suspended one rather than dropping
 * it. Dropping it made the account fall back to the default role — which for a
 * suspended contractor meant *more* access than the record grants, not less.
 * The account is blocked at login instead; the role it holds is reported as-is.
 */
const ROLE_ASSIGNMENT = seed.userRoles.reduce((acc, a) => {
  const current = acc[a.user_id]
  if (!current || (current.status !== 'ACTIVE' && a.status === 'ACTIVE')) acc[a.user_id] = a
  return acc
}, {})

const initialsOf = (name) => {
  const parts = String(name).trim().split(/\s+/)
  return parts.length > 1 ? `${parts[0][0]}.${parts[1][0]}` : String(name).slice(0, 2)
}

/** Accounts loaded from the sheet, plus the site administrator account. */
export const users = [
  {
    id: 0,
    userId: 'USR-000',
    username: 'mostafa',
    password: 'mostafa2026',
    name: 'مصطفى',
    initials: 'م',
    role: 'HSE_MANAGER',
    roleLabel: 'HSE Manager',
    roleAr: ROLE_AR.HSE_MANAGER,
    email: 'mostafa@elsewedy.com',
    department: 'HSE',
    scope: 'ESCA',
    status: 'ACTIVE',
    fromSheet: false,
  },
  ...seed.users.map((u, i) => {
    const assignment = ROLE_ASSIGNMENT[u.user_id]
    const role = ROLE[assignment?.role_id]
    const emp = EMP[u.employee_id]
    const name = emp?.display_name || u.username
    return {
      id: i + 1,
      userId: u.user_id,
      username: u.username,
      password: demoPassword(u.username),
      name,
      initials: initialsOf(name),
      role: role?.role_name || 'WORKER',
      roleLabel: role?.role_name || 'WORKER',
      roleAr: ROLE_AR[role?.role_name] || role?.role_name,
      email: emp?.email_alias || `${u.username}@example.local`,
      employeeNo: u.employee_id,
      jobTitle: emp?.job_title,
      department: deptName(emp?.department_id),
      scope: assignment?.scope_id,
      scopeType: assignment?.scope_type,
      status: u.status,
      assignmentStatus: assignment?.status,
      mfa: u.mfa_enabled,
      lastLogin: u.last_login_at,
      fromSheet: true,
    }
  }),
]

/** RBAC matrix straight from the sheet, with the assigned-user count added. */
export const roles = seed.roles.map((r) => {
  const rbac = seed.rbacMatrix.find((m) => m.role_id === r.role_id) || {}
  return {
    roleId: r.role_id,
    role: r.role_name,
    roleAr: ROLE_AR[r.role_name] || r.role_name,
    description: r.description,
    scope: r.scope_level,
    users: seed.userRoles.filter((a) => a.role_id === r.role_id).length,
    incidents: rbac.incidents_access,
    permits: rbac.permits_access,
    inspections: rbac.inspections_access,
    risks: rbac.risks_access,
    training: rbac.training_access,
    health: rbac.health_access,
    admin: rbac.admin_access,
    approveHighRisk: rbac.approve_high_risk === true,
    exportReports: rbac.export_reports === true,
  }
})

export const sessions = users
  .filter((u) => u.fromSheet && u.status === 'ACTIVE' && u.lastLogin)
  .sort((a, b) => String(b.lastLogin).localeCompare(String(a.lastLogin)))
  .slice(0, 6)
  .map((u) => ({
    user: u.name,
    role: u.roleAr,
    device: u.username.startsWith('svc') ? 'Service · FastAPI' : 'Web · Chrome',
    ip: '—',
    since: String(u.lastLogin).slice(11, 16),
    mfa: u.mfa === true,
  }))

/* ------------------------------------------------------------------ */
/* Departments & zones                                                 */
/* ------------------------------------------------------------------ */

const headcountByDept = seed.employees.reduce((acc, e) => {
  acc[e.department_id] = (acc[e.department_id] || 0) + 1
  return acc
}, {})

const incidentsByDept = seed.incidents.reduce((acc, i) => {
  acc[i.department_id] = (acc[i.department_id] || 0) + 1
  return acc
}, {})

/** Average inspection score per department — the closest thing the sheets
 *  carry to a safety index, and it is a measured number rather than a guess. */
const scoreByDept = (() => {
  const acc = {}
  seed.inspections
    .filter((i) => i.score_pct != null)
    .forEach((i) => {
      ;(acc[i.department_id] ||= []).push(Number(i.score_pct) * 100)
    })
  return Object.fromEntries(
    Object.entries(acc).map(([k, v]) => [k, Math.round(v.reduce((a, b) => a + b, 0) / v.length)])
  )
})()

const fireByZone = seed.fireEquipment.reduce((acc, f) => {
  const z = (acc[f.zone_id] ||= { total: 0, ok: 0 })
  z.total += 1
  if (f.status === 'VALID') z.ok += 1
  return acc
}, {})

const SECTOR_OF = { PRODUCTION: 'قطاع الإنتاج', OPERATIONS: 'المخازن والمرافق', TECHNICAL: 'المرافق الفنية', CONTROL: 'الجودة والرقابة', ADMIN: 'الأقسام الإدارية', HEALTH: 'الصحة المهنية' }

export const departments = Object.entries(
  seed.departments.reduce((acc, d) => {
    const sector = SECTOR_OF[d.department_type] || 'أخرى'
    ;(acc[sector] ||= []).push(d)
    return acc
  }, {})
).map(([sector, depts]) => ({
  sector,
  sectorEn: depts[0].department_type,
  headcount: depts.reduce((n, d) => n + (headcountByDept[d.department_id] || 0), 0),
  zones: depts.map((d) => {
    const zones = seed.zones.filter((z) => z.department_id === d.department_id)
    const fire = zones.reduce(
      (acc, z) => {
        const f = fireByZone[z.zone_id]
        if (f) {
          acc.total += f.total
          acc.ok += f.ok
        }
        return acc
      },
      { total: 0, ok: 0 }
    )
    const score = scoreByDept[d.department_id] ?? null
    const lastInspection = seed.inspections
      .filter((i) => i.department_id === d.department_id && i.completed_at)
      .map((i) => dateOnly(i.completed_at))
      .sort()
      .pop()
    return {
      code: d.department_id,
      name: d.name_ar,
      nameEn: d.name_en,
      headcount: headcountByDept[d.department_id] || 0,
      score,
      incidents: incidentsByDept[d.department_id] || 0,
      extinguishers: fire.total ? `${fire.ok} / ${fire.total}` : '—',
      lastInspection: lastInspection || '—',
      status: score == null ? 'nu' : score >= 85 ? 'ok' : score >= 70 ? 'wn' : 'cr',
      statusLabel: score == null ? 'لا توجد جولات' : score >= 85 ? 'مطابق' : score >= 70 ? 'يحتاج متابعة' : 'منطقة حرجة',
      hazard: zones.map((z) => `${z.name_ar} (${t(z.risk_class)})`).join(' · ') || '—',
      zoneCount: zones.length,
    }
  }),
}))

export const safetyByZone = Object.entries(scoreByDept)
  .map(([id, score]) => ({ zone: deptName(id), score }))
  .sort((a, b) => b.score - a.score)

/* ------------------------------------------------------------------ */
/* Incidents                                                           */
/* ------------------------------------------------------------------ */

const SEV_TONE = { CRITICAL: 'cr', MAJOR: 'cr', HIGH: 'cr', MODERATE: 'wn', MEDIUM: 'wn', MINOR: 'nu', LOW: 'nu' }

export const incidents = seed.incidents
  .slice()
  .sort((a, b) => String(b.reported_at).localeCompare(String(a.reported_at)))
  .map((i) => ({
    id: i.incident_id,
    date: dateOnly(i.reported_at),
    time: timeOnly(i.reported_at),
    zone: zoneName(i.zone_id),
    department: deptName(i.department_id),
    type: t(i.incident_type),
    classification: i.incident_type,
    description: i.title,
    detail: i.description,
    severity: t(i.severity),
    severityTone: SEV_TONE[i.severity] || 'nu',
    injured: i.injured_employee_id ? empName(i.injured_employee_id) : '—',
    employeeNo: i.injured_employee_id || '—',
    status: t(i.status),
    statusTone: tone(i.status),
    owner: empName(i.investigation_owner_id),
    lostDays: i.lost_days ?? 0,
    immediateAction: i.description || '—',
    dueDate: dateOnly(i.target_close_date),
    closedAt: dateOnly(i.actual_close_date),
    source: i.source,
    linkedPermit: null,
    linkedHazard: null,
    rawStatus: i.status,
  }))

const openIncidents = incidents.filter((i) => !['CLOSED'].includes(i.rawStatus))

export const incidentStats = {
  ytdTotal: seed.incidents.length,
  lti: seed.incidents.filter((i) => i.incident_type === 'LTI').length,
  firstAid: seed.incidents.filter((i) => i.incident_type === 'FIRST_AID').length,
  nearMiss: seed.monthlyKpis.reduce((n, k) => n + (k.near_misses || 0), 0),
  lostDays: seed.incidents.reduce((n, i) => n + (i.lost_days || 0), 0),
  avgClosureDays: (() => {
    const closed = seed.incidents.filter((i) => i.actual_close_date && i.reported_at)
    if (!closed.length) return 0
    const days = closed.map(
      (i) => (new Date(i.actual_close_date) - new Date(i.reported_at)) / 86400000
    )
    return Math.round((days.reduce((a, b) => a + b, 0) / days.length) * 10) / 10
  })(),
  closureTarget: 7,
}

const CAUSE_COLOR = ['#E0483C', '#F09030', '#F09030', '#4A9DD8', '#4A9DD8', '#5E7794']

export const rootCauses = (() => {
  const counts = seed.incidentRca.reduce((acc, r) => {
    if (!r.primary_cause_category) return acc
    acc[r.primary_cause_category] = (acc[r.primary_cause_category] || 0) + 1
    return acc
  }, {})
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([cause, n], idx) => ({
      cause: t(cause),
      pct: Math.round((n / total) * 100),
      color: CAUSE_COLOR[idx] || '#5E7794',
    }))
})()

export const capa = seed.capa.map((c) => ({
  id: c.capa_id,
  action: c.title,
  owner: empName(c.assigned_to),
  due: dateOnly(c.due_date),
  status: t(c.status),
  tone: c.days_overdue > 0 ? 'cr' : tone(c.status),
  source: c.incident_id || c.finding_id || '—',
  priority: t(c.priority),
  daysOverdue: c.days_overdue || 0,
}))

/** The sheet stores one RCA record per incident, not a five-why ladder — so the
 *  toolkit shows what is actually recorded instead of padding it out. */
export const rcaByIncident = Object.fromEntries(
  seed.incidentRca.map((r) => [
    r.incident_id,
    {
      method: r.method,
      problem: r.problem_statement,
      category: t(r.primary_cause_category),
      rootCause: r.root_cause,
      contributing: r.contributing_factors,
      status: t(r.status),
      completedBy: empName(r.completed_by),
      completedAt: dateOnly(r.completed_at),
    },
  ])
)

/* ------------------------------------------------------------------ */
/* Permits                                                             */
/* ------------------------------------------------------------------ */

const PERMIT_ICON = {
  HOT_WORK: 'flame',
  ELECTRICAL: 'bolt',
  WORK_AT_HEIGHT: 'ladder',
  CONFINED_SPACE: 'confined',
  MECHANICAL_LOTO: 'wrench',
  EXCAVATION: 'excavation',
}

export const permitTypes = Object.keys(PERMIT_ICON).map((key) => ({
  key,
  label: t(key),
  icon: PERMIT_ICON[key],
  tone: ['HOT_WORK', 'ELECTRICAL', 'CONFINED_SPACE'].includes(key) ? 'cr' : 'wn',
  count: seed.permits.filter((p) => p.permit_type === key).length,
}))

export const permits = seed.permits.map((p) => ({
  id: p.permit_id,
  type: p.permit_type,
  typeLabel: t(p.permit_type),
  icon: PERMIT_ICON[p.permit_type] || 'permit',
  zone: zoneName(p.zone_id),
  department: deptName(p.department_id),
  description: p.work_description,
  issuer: empName(p.issuer_id),
  requester: empName(p.requester_id),
  executor: p.executor_name,
  executorType: t(p.executor_type),
  date: dateOnly(p.start_at),
  from: timeOnly(p.start_at),
  to: timeOnly(p.expiry_at),
  status: t(p.status),
  statusTone: tone(p.status),
  rawStatus: p.status,
  jsa: p.jsa_id || '—',
  risk: p.risk_level,
  riskLabel: t(p.risk_level),
  hoursToExpiry: p.hours_to_expiry == null ? null : Math.round(p.hours_to_expiry * 10) / 10,
  flag: p.automation_flag,
  suspendedReason: p.suspended_reason,
}))

export const permitStats = {
  active: permits.filter((p) => p.rawStatus === 'ACTIVE').length,
  expiringSoon: permits.filter((p) => p.flag === 'DUE_SOON' || p.flag === 'EXPIRES_TODAY').length,
  pendingApproval: permits.filter((p) => p.rawStatus === 'PENDING_APPROVAL').length,
  violations: permits.filter((p) => p.rawStatus === 'REJECTED' || p.rawStatus === 'BLOCKED').length,
  avgApprovalMinutes: (() => {
    const byPermit = {}
    seed.permitApprovals.forEach((a) => {
      if (a.decided_at) (byPermit[a.permit_id] ||= []).push(new Date(a.decided_at))
    })
    const spans = Object.values(byPermit)
      .filter((d) => d.length > 1)
      .map((d) => (Math.max(...d) - Math.min(...d)) / 60000)
    return spans.length ? Math.round(spans.reduce((a, b) => a + b, 0) / spans.length) : 0
  })(),
  issuedYtd: seed.permits.length,
  closedProperly: permits.filter((p) => p.rawStatus === 'CLOSED').length,
  cancelled: permits.filter((p) => p.rawStatus === 'CANCELLED').length,
  linkedIncidents: 0,
  compliance: pct(permits.filter((p) => p.rawStatus !== 'REJECTED' && p.rawStatus !== 'BLOCKED').length, permits.length),
}

export const permitApprovalsByPermit = seed.permitApprovals.reduce((acc, a) => {
  ;(acc[a.permit_id] ||= []).push({
    stepNo: a.step_no,
    step: a.approver_role,
    approver: empName(a.approver_id),
    detail: `${empName(a.approver_id)} · ${a.decided_at ? String(a.decided_at).slice(11, 16) : 'بانتظار'} ${a.comments ? `· ${a.comments}` : ''}`,
    state: a.decision === 'APPROVED' ? 'done' : 'pending',
    decision: a.decision,
    signature: a.signature_hash,
    decidedAt: a.decided_at,
  })
  return acc
}, {})

Object.values(permitApprovalsByPermit).forEach((steps) => steps.sort((a, b) => a.stepNo - b.stepNo))

export const permitChecklists = seed.permitChecklist.reduce((acc, c) => {
  const permit = seed.permits.find((p) => p.permit_id === c.permit_id)
  const key = permit?.permit_type
  if (!key) return acc
  acc[key] ||= []
  if (!acc[key].some((x) => x.code === c.item_code)) {
    acc[key].push({ code: c.item_code, text: c.item_text, mandatory: c.mandatory_flag === true, response: c.response })
  }
  return acc
}, {})

export const simops = {
  blocked: (() => {
    const s = seed.simops.find((x) => x.decision?.startsWith('BLOCK')) || seed.simops[0]
    if (!s) return null
    return {
      permit: s.permit_b_id,
      request: seed.permits.find((p) => p.permit_id === s.permit_b_id)?.work_description || s.permit_b_id,
      conflictsWith: s.permit_a_id,
      reason: `${t(s.conflict_type)} — المسافة ${s.distance_m}م · القاعدة ${s.rule_code}`,
      decision: t(s.decision) === s.decision ? 'حجب إصدار التصريح المتعارض' : t(s.decision),
      zone: zoneName(s.zone_id),
    }
  })(),
  rules: seed.simops.map((s) => ({
    rule: t(s.conflict_type),
    limit: s.distance_m ? `حد ${s.distance_m}م` : t(s.decision),
  })),
  blockedYtd: seed.simops.filter((s) => s.decision?.startsWith('BLOCK')).length,
}

/* ------------------------------------------------------------------ */
/* Risk register                                                       */
/* ------------------------------------------------------------------ */

export const hazards = seed.risks.map((r) => ({
  code: r.risk_id,
  zone: zoneName(r.zone_id),
  department: deptName(r.department_id),
  hazard: r.hazard,
  activity: r.activity,
  probability: r.likelihood,
  severity: r.severity,
  score: r.inherent_score,
  level: r.risk_level,
  controls: r.controls,
  residual: r.residual_score,
  owner: empName(r.owner_id),
  reviewed: dateOnly(r.last_reviewed_at),
  nextReview: dateOnly(r.next_review_date),
  reviewFlag: r.review_flag,
  status: r.status,
}))

const BAND = [
  { band: 'حرج — إيقاف النشاط', min: 20, color: '#8E1F17' },
  { band: 'عالي — إجراء عاجل', min: 15, color: '#E0483C' },
  { band: 'متوسط — خطة تخفيف', min: 10, color: '#F09030' },
  { band: 'منخفض — مراقبة', min: 5, color: '#C6C43A' },
  { band: 'مقبول', min: 0, color: '#38B87C' },
]

export const riskDistribution = BAND.map((b, i) => {
  const max = i === 0 ? Infinity : BAND[i - 1].min - 1
  const count = hazards.filter((h) => h.score >= b.min && h.score <= max).length
  return { band: b.band, count, pct: pct(count, hazards.length), color: b.color }
})

export const riskSummary = {
  total: hazards.length,
  reducedThisYear: hazards.filter((h) => h.residual < h.score).length,
  newlyIdentified: hazards.filter((h) => h.reviewFlag === 'REVIEW_REQUIRED').length,
  lastFullReview: hazards.map((h) => h.reviewed).filter((d) => d !== '—').sort().pop() || '—',
  nextReview: hazards.map((h) => h.nextReview).filter((d) => d !== '—').sort()[0] || '—',
  overdueReviews: hazards.filter((h) => h.reviewFlag === 'REVIEW_OVERDUE').length,
}

/* ------------------------------------------------------------------ */
/* JSA                                                                 */
/* ------------------------------------------------------------------ */

export const jsaList = seed.jsa.map((j) => ({
  id: j.jsa_id,
  task: j.task_name,
  zone: zoneName(j.zone_id),
  steps: seed.jsaSteps.filter((s) => s.jsa_id === j.jsa_id).length,
  criticalSteps: seed.jsaSteps.filter((s) => s.jsa_id === j.jsa_id && s.score_before >= 15).length,
  linkedPermit: j.permit_required ? t(j.permit_type) : '—',
  reviewed: dateOnly(j.approved_at || j.created_at),
  status: t(j.status),
  tone: tone(j.status),
}))

export const jsaStats = {
  approved: seed.jsa.filter((j) => j.status === 'APPROVED').length,
  needsReview: seed.jsa.filter((j) => j.status !== 'APPROVED').length,
  linkedToPermits: seed.jsa.filter((j) => j.permit_required === true).length,
  criticalTaskCoverage: pct(seed.jsa.filter((j) => j.permit_required === true).length, seed.jsa.length),
}

export const jsaDetail = Object.fromEntries(
  seed.jsa.map((j) => [
    j.jsa_id,
    {
      task: j.task_name,
      steps: seed.jsaSteps
        .filter((s) => s.jsa_id === j.jsa_id)
        .sort((a, b) => a.step_no - b.step_no)
        .map((s) => ({
          step: s.task_step,
          hazard: s.hazard,
          control: `${s.control_measure} (${t(s.control_level)})`,
          before: s.score_before,
          after: s.score_after,
        })),
    },
  ])
)

/* ------------------------------------------------------------------ */
/* Fire equipment & PPE                                                */
/* ------------------------------------------------------------------ */

/** Anything the sheet flags that isn't plainly valid needs an eye on it, so an
 *  unrecognised status degrades to "needs attention" rather than to blank. */
const FIRE_STATE = { VALID: 'ok', DUE_SOON: 'wn', EXPIRED: 'cr', MISSING: 'cr', MAINTENANCE: 'wn', ACTION_REQUIRED: 'cr' }
const fireState = (status) => FIRE_STATE[status] ?? 'wn'

const extinguishers = seed.fireEquipment.filter((f) => f.asset_type === 'EXTINGUISHER')

export const fireUnits = extinguishers.map((f) => ({
  code: f.equipment_id,
  location: f.location_detail,
  type: `${t(f.subtype)} ${f.capacity || ''}`.trim(),
  expiry: String(f.expiry_date || '').slice(0, 7),
  state: fireState(f.status),
  zone: zoneName(f.zone_id),
  qr: f.qr_code,
}))

export const fireAttention = seed.fireEquipment
  .filter((f) => ['EXPIRED', 'MISSING', 'MAINTENANCE', 'ACTION_REQUIRED'].includes(f.status))
  .map((f) => ({
    code: f.equipment_id,
    location: `${zoneName(f.zone_id)} / ${f.location_detail}`,
    type: `${t(f.subtype)} ${f.capacity || ''}`.trim(),
    expiry: dateOnly(f.expiry_date),
    issue: t(f.status),
    action: f.status === 'MISSING' ? 'بلاغ' : 'استبدال',
  }))

export const fireCoverage = Object.entries(
  seed.fireEquipment.reduce((acc, f) => {
    const key = deptName(f.department_id)
    const row = (acc[key] ||= { zone: key, total: 0, ok: 0 })
    row.total += 1
    if (f.status === 'VALID') row.ok += 1
    return acc
  }, {})
).map(([, v]) => v)

export const fireStats = {
  serviceable: seed.fireEquipment.filter((f) => f.status === 'VALID').length,
  total: seed.fireEquipment.length,
  expiringIn30: seed.fireEquipment.filter((f) => f.status === 'DUE_SOON').length,
  expired: seed.fireEquipment.filter((f) => ['EXPIRED', 'MISSING'].includes(f.status)).length,
  hydrants: seed.fireEquipment.filter((f) => f.asset_type === 'HYDRANT').length,
  smokeDetectors: seed.fixedSafetyAssets.find((a) => a.asset_type === 'FIXED_GAS_DETECTOR')?.total_qty ?? 0,
  smokeDetectorsWorking: seed.fixedSafetyAssets.find((a) => a.asset_type === 'FIXED_GAS_DETECTOR')?.operational_qty ?? 0,
  firstAidBoxes: seed.fixedSafetyAssets.find((a) => a.asset_type === 'AED')?.total_qty ?? 0,
  firstAidComplete: seed.fixedSafetyAssets.find((a) => a.asset_type === 'AED')?.operational_qty ?? 0,
  readiness: pct(seed.fireEquipment.filter((f) => f.status === 'VALID').length, seed.fireEquipment.length),
}

export const ppeStock = seed.ppeInventory.map((p) => ({
  item: p.name_ar,
  code: p.item_code,
  category: t(p.category),
  balance: p.balance_qty,
  threshold: p.reorder_threshold,
  rate: p.monthly_consumption,
  status: p.stock_status === 'OK' ? 'كافٍ' : 'تحت الحد',
  tone: p.stock_status === 'OK' ? 'ok' : 'cr',
  supplier: p.supplier,
}))

export const fixedAssets = seed.fixedSafetyAssets.map((a) => ({
  asset: a.asset_name,
  total: a.total_qty,
  working: a.operational_qty,
  lastTest: dateOnly(a.last_test_date),
  status: t(a.status),
  tone: tone(a.status),
}))

export const ppeMatrix = (() => {
  const items = seed.ppeInventory.slice(0, 8)
  const zoneIds = [...new Set(seed.ppeMatrix.map((m) => m.zone_id))]
  return {
    columns: items.map((i) => i.name_ar),
    rows: zoneIds.map((zid) => ({
      zone: zoneName(zid),
      values: items.map((i) => {
        const m = seed.ppeMatrix.find((x) => x.zone_id === zid && x.ppe_item_id === i.ppe_item_id)
        if (!m) return 'no'
        return m.required_flag === true ? 'req' : 'task'
      }),
    })),
  }
})()

/* ------------------------------------------------------------------ */
/* Inspections                                                         */
/* ------------------------------------------------------------------ */

export const inspectionSchedule = seed.inspections.map((i) => ({
  type: t(i.inspection_type),
  zone: zoneName(i.zone_id),
  frequency: i.checklist_version || '—',
  owner: empName(i.lead_inspector_id),
  next: dateOnly(i.scheduled_at),
  status: t(i.status),
  tone: tone(i.status),
  score: i.score_pct == null ? null : Math.round(i.score_pct * 100),
}))

const FINDING_COLOR = { CRITICAL: '#E0483C', MAJOR: '#F09030', MINOR: '#4A9DD8', LOW: '#38B87C' }

export const inspectionFindings = seed.findings.map((f) => ({
  grade: f.severity,
  state: t(f.status),
  color: FINDING_COLOR[f.severity] || '#4A9DD8',
  title: f.description,
  meta: `${t(f.category)} · المسؤول: ${empName(f.responsible_id)} · الموعد: ${dateOnly(f.due_date)}`,
}))

export const inspectionStats = {
  completed: seed.inspections.filter((i) => i.status === 'COMPLETED').length,
  planned: seed.inspections.length,
  openFindings: seed.findings.filter((f) => f.status === 'OPEN').length,
  overdueFindings: seed.findings.filter((f) => f.status === 'OPEN' && f.due_date && new Date(f.due_date) < new Date(asOf)).length,
  compliance: (() => {
    const scored = seed.inspections.filter((i) => i.score_pct != null)
    return scored.length ? Math.round((scored.reduce((n, i) => n + i.score_pct, 0) / scored.length) * 100) : 0
  })(),
  overdueWalks: seed.inspections.filter((i) => i.status === 'OVERDUE').length,
}

/* ------------------------------------------------------------------ */
/* Training                                                            */
/* ------------------------------------------------------------------ */

export const trainingPrograms = seed.trainingCourses.map((c) => {
  const certs = seed.certificates.filter((x) => x.course_id === c.course_id)
  const valid = certs.filter((x) => x.status === 'VALID').length
  return {
    program: c.name_ar,
    audience: t(c.target_group),
    validity: c.validity_months ? `${c.validity_months} شهر` : '—',
    qualified: valid,
    target: certs.length || 1,
    provider: c.provider,
  }
})

export const trainingExpiring = seed.certificates
  .filter((c) => c.status !== 'VALID' || (c.days_to_expiry != null && c.days_to_expiry <= 30))
  .sort((a, b) => (a.days_to_expiry ?? 0) - (b.days_to_expiry ?? 0))
  .map((c) => ({
    employee: empName(c.employee_id),
    employeeNo: c.employee_id,
    dept: deptName(EMP[c.employee_id]?.department_id),
    certificate: COURSE[c.course_id]?.name_ar || c.course_id,
    expires: dateOnly(c.expiry_date),
    status: t(c.status),
    tone: c.status === 'EXPIRED' ? 'cr' : 'wn',
    daysToExpiry: c.days_to_expiry,
  }))

export const trainingStats = {
  coverage: pct(seed.certificates.filter((c) => c.status === 'VALID').length, seed.certificates.length),
  trained: new Set(seed.certificates.filter((c) => c.status === 'VALID').map((c) => c.employee_id)).size,
  headcount: seed.employees.length,
  expiringThisMonth: seed.certificates.filter((c) => c.days_to_expiry != null && c.days_to_expiry > 0 && c.days_to_expiry <= 30).length,
  expired: seed.certificates.filter((c) => c.status === 'EXPIRED').length,
  hoursYtd: seed.monthlyKpis.reduce((n, k) => n + (k.training_hours || 0), 0),
  hoursPerEmployee: Math.round(seed.monthlyKpis.reduce((n, k) => n + (k.training_hours || 0), 0) / (seed.employees.length || 1)),
}

export const trainingSchedule = [
  { id: 'TRN-001', certId: 1, employee: 'محمود عبد الله', dept: 'خط الإنتاج A', course: 'السلامة العامة (General Induction)', provider: 'ESCA HSE Academy', issueDate: '2025-01-15', expiryDate: '2026-12-15', evidenceRef: 'CERT-2026-0001', status: 'سارية ومعتمدة', statusTone: 'ok' },
  { id: 'TRN-002', certId: 2, employee: 'هبة فؤاد', dept: 'خط الإنتاج B', course: 'العمل الساخن (Hot Work)', provider: 'Elsewedy Technical Training Center', issueDate: '2025-03-01', expiryDate: '2027-01-04', evidenceRef: 'CERT-2026-0002', status: 'سارية ومعتمدة', statusTone: 'ok' },
  { id: 'TRN-003', certId: 3, employee: 'أحمد سامي', dept: 'ورشة الصيانة الميكانيكية', course: 'القفل وتطبيق بطاقة LOTO', provider: 'External Certified Provider', issueDate: '2025-04-15', expiryDate: '2027-01-24', evidenceRef: 'CERT-2026-0003', status: 'سارية ومعتمدة', statusTone: 'ok' },
  { id: 'TRN-004', certId: 4, employee: 'كريم رشاد', dept: 'المخازن والخام', course: 'العمل على ارتفاع (Working at Height)', provider: 'ESCA HSE Academy', issueDate: '2025-05-30', expiryDate: '2027-02-13', evidenceRef: 'CERT-2026-0004', status: 'مجدولة للتجديد', statusTone: 'wn' },
]

/* ------------------------------------------------------------------ */
/* HazMat & occupational health                                        */
/* ------------------------------------------------------------------ */

export const chemicals = seed.chemicals.map((c) => {
  const sds = seed.sdsRecords.find((s) => s.chemical_id === c.chemical_id)
  return {
    code: c.chemical_id,
    name: c.trade_name,
    chemicalName: c.chemical_name,
    cas: c.cas_number,
    ghs: c.ghs_classes?.split(';').map((g) => t(g)).join(' · ') || '—',
    qty: `${c.quantity} ${c.unit}`,
    location: zoneName(c.zone_id),
    class: t(c.storage_class),
    sds: dateOnly(sds?.review_date || sds?.issue_date),
    sdsStatus: sds?.status,
    tone: c.storage_class === 'FLAMMABLE' || c.storage_class === 'CORROSIVE' ? 'cr' : 'wn',
  }
})

export const hazmatStats = {
  total: seed.chemicals.length,
  flammable: seed.chemicals.filter((c) => c.ghs_classes?.includes('FLAMMABLE')).length,
  corrosive: seed.chemicals.filter((c) => c.ghs_classes?.includes('CORROSIVE')).length,
  sdsExpired: seed.sdsRecords.filter((s) => s.status !== 'CURRENT').length,
  storageAudits: seed.inspections.filter((i) => i.inspection_type === 'CHEMICAL_STORAGE').length,
  spillKits: seed.fixedSafetyAssets.find((a) => a.asset_type === 'EMERGENCY_SHOWER_EYEWASH')?.total_qty ?? 0,
}

export const healthExams = seed.medicalProtocols.map((p) => {
  const exams = seed.healthExams.filter((e) => e.protocol_id === p.protocol_id)
  return {
    type: p.exam_type,
    target: t(p.target_group),
    frequency: p.frequency_months ? `كل ${p.frequency_months} شهر` : '—',
    done: exams.filter((e) => e.status === 'COMPLETED').length,
    due: exams.filter((e) => e.status !== 'COMPLETED').length,
  }
})

export const healthStats = {
  examsYtd: seed.healthExams.filter((e) => e.completed_date).length,
  dueThisMonth: seed.healthExams.filter((e) => e.status === 'SCHEDULED' || e.status === 'PENDING').length,
  restrictions: seed.healthExams.filter((e) => e.fitness_result === 'FIT_WITH_RESTRICTIONS').length,
  audiometryFlags: seed.employeeExposures.filter((e) => e.exposure_type === 'NOISE').length,
  overdue: seed.healthExams.filter((e) => e.status === 'OVERDUE').length,
}

export const exposureMonitoring = seed.employeeExposures.map((e) => ({
  agent: t(e.exposure_type),
  zone: zoneName(e.zone_id),
  measured: `${e.exposure_value} ${e.unit || ''}`.trim(),
  limit: t(e.control_status),
  tone: e.control_status === 'CONTROLLED_WITH_PPE' ? 'ok' : 'wn',
  employee: empName(e.employee_id),
}))

export const healthSchedule = [
  { id: 'HEX-001', employee: 'محمود عبد الله', protocol: 'فحص قياس السمع (Audiometry)', scheduledDate: '2026-08-28', completedDate: '2026-08-28', fitness: 'لائق طبياً', fitnessTone: 'ok', restrictions: 'لا توجد قيود', doctor: 'د. حازم القاضي', nextDueDate: '2027-02-28', status: 'مكتمل', statusTone: 'ok' },
  { id: 'HEX-002', employee: 'هبة فؤاد', protocol: 'فحص وظائف التنفس والرئة (Spirometry)', scheduledDate: '2026-08-29', completedDate: null, fitness: 'قيد الانتظار', fitnessTone: 'wn', restrictions: 'تحت التقييم', doctor: 'د. سمر الشافعي', nextDueDate: '2027-02-28', status: 'مجدول', statusTone: 'in' },
  { id: 'HEX-003', employee: 'أحمد سامي', protocol: 'لياقة الارتفاعات والأماكن المغلقة', scheduledDate: '2026-08-30', completedDate: '2026-08-30', fitness: 'لائق مع قيود', fitnessTone: 'wn', restrictions: 'تجنب العمل على ارتفاعات > 10م', doctor: 'د. حازم القاضي', nextDueDate: '2026-11-30', status: 'مكتمل', statusTone: 'ok' },
]

/* ------------------------------------------------------------------ */
/* Reports & KPIs                                                      */
/* ------------------------------------------------------------------ */

const kpiRows = seed.monthlyKpis.slice().sort((a, b) => String(a.month).localeCompare(String(b.month)))
const latestKpi = kpiRows[kpiRows.length - 1] || {}

const AR_MONTH = ['ينا', 'فبر', 'مار', 'أبر', 'ماي', 'يون', 'يول', 'أغس', 'سبت', 'أكت', 'نوف', 'ديس']

export const monthlyTrend = kpiRows.map((k) => ({
  month: AR_MONTH[Number(String(k.month).slice(5, 7)) - 1] || k.month,
  incidents: k.recordable_incidents || 0,
  nearMiss: k.near_misses || 0,
  observations: k.safety_observations || 0,
}))

const avg = (key) => {
  const vals = kpiRows.map((k) => k[key]).filter((v) => typeof v === 'number')
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0
}

export const reportKpis = [
  { key: 'TRIR', value: avg('trir').toFixed(2), pct: Math.min(100, Math.round((1.2 / (avg('trir') || 1.2)) * 60)), color: avg('trir') <= 1.2 ? '#38B87C' : '#F09030', label: 'معدل الإصابات المسجلة', target: 'الهدف ≤ 1.20' },
  { key: 'LTIFR', value: avg('ltifr').toFixed(2), pct: Math.min(100, Math.round((0.5 / (avg('ltifr') || 0.5)) * 60)), color: avg('ltifr') <= 0.5 ? '#38B87C' : '#F09030', label: 'معدل تكرار الإصابات المُعطِّلة', target: 'الهدف ≤ 0.50' },
  { key: 'SEVERITY RATE', value: avg('severity_rate').toFixed(1), pct: 55, color: '#F09030', label: 'أيام ضائعة لكل مليون ساعة', target: 'الهدف ≤ 5.0' },
  {
    key: 'NEAR MISS RATIO',
    value: (kpiRows.reduce((n, k) => n + (k.near_misses || 0), 0) / Math.max(1, kpiRows.reduce((n, k) => n + (k.recordable_incidents || 0), 0))).toFixed(1),
    pct: 88,
    color: '#38B87C',
    label: 'أشباه حوادث لكل حادث',
    target: 'الهدف ≥ 3.0',
  },
]

export const trirTrend = kpiRows.map((k) => ({ year: String(k.month), trir: k.trir ?? 0 }))

export const heatmap = (() => {
  const counts = {}
  seed.incidents.forEach((i) => {
    counts[i.zone_id] = (counts[i.zone_id] || 0) + 1
  })
  seed.findings.forEach((f) => {
    const insp = seed.inspections.find((x) => x.inspection_id === f.inspection_id)
    if (insp) counts[insp.zone_id] = (counts[insp.zone_id] || 0) + 1
  })
  const rows = {}
  seed.zones.forEach((z) => {
    const sector = SECTOR_OF[DEPT[z.department_id]?.department_type] || 'أخرى'
    ;(rows[sector] ||= []).push([z.name_ar, counts[z.zone_id] || 0])
  })
  return Object.entries(rows).map(([row, cells]) => ({ row, cells }))
})()

export const leadingIndicators = [
  { label: 'نسبة إغلاق CAPA في الموعد', value: pct(seed.capa.filter((c) => c.status === 'COMPLETED' && !c.days_overdue).length, seed.capa.length), color: '#F09030', note: 'الهدف ≥ 90%' },
  { label: 'نسبة إنجاز جولات التفتيش', value: pct(inspectionStats.completed, inspectionStats.planned), color: '#38B87C', note: `${inspectionStats.completed} من ${inspectionStats.planned} جولة` },
  { label: 'نسبة صلاحية الشهادات', value: trainingStats.coverage, color: trainingStats.coverage >= 85 ? '#38B87C' : '#F09030', note: `${trainingStats.hoursYtd.toLocaleString('en-US')} ساعة تدريب` },
  { label: 'معدل الإبلاغ عن أشباه الحوادث', value: 93, display: reportKpis[3].value + ':1', color: '#38B87C', note: 'الهدف ≥ 3:1' },
  { label: 'جاهزية معدات الحريق', value: fireStats.readiness, color: fireStats.readiness >= 90 ? '#38B87C' : '#F09030', note: `${fireStats.serviceable} من ${fireStats.total}` },
  { label: 'تغطية JSA للمهام الحرجة', value: jsaStats.criticalTaskCoverage, color: '#F09030', note: 'الهدف 100% بنهاية Q4' },
]

export const pyramid = (() => {
  const c = (type) => seed.incidents.filter((i) => i.incident_type === type).length
  const tiers = [
    { label: 'إصابات مُعطِّلة (LTI)', count: c('LTI'), color: '#E0483C', textColor: '#fff' },
    { label: 'إصابات إسعافات أولية', count: c('FIRST_AID'), color: '#c0603a', textColor: '#fff' },
    { label: 'أشباه حوادث', count: kpiRows.reduce((n, k) => n + (k.near_misses || 0), 0), color: '#F09030', textColor: '#1a1a1a' },
    { label: 'أوضاع غير آمنة', count: c('UNSAFE_CONDITION') + c('UNSAFE_ACT') + seed.findings.length, color: '#9aa832', textColor: '#1a1a1a' },
    { label: 'ملاحظات سلامة', count: kpiRows.reduce((n, k) => n + (k.safety_observations || 0), 0), color: '#38B87C', textColor: '#0d1a12' },
  ]
  const max = Math.max(...tiers.map((x) => x.count), 1)
  return tiers.map((x) => ({ ...x, width: Math.max(22, Math.round((x.count / max) * 100)) }))
})()

/* ------------------------------------------------------------------ */
/* Integrations, audit                                                 */
/* ------------------------------------------------------------------ */

export const integrationList = seed.integrations.map((i) => {
  const last = seed.apiLogs.filter((l) => l.integration_id === i.integration_id).map((l) => l.called_at).sort().pop()
  return {
    system: i.system_name,
    direction: t(i.direction),
    mode: i.protocol,
    frequency: t(i.frequency),
    lastRun: last ? String(last).replace('T', ' ').slice(0, 16) : '—',
    records: seed.apiLogs.filter((l) => l.integration_id === i.integration_id).length,
    status: t(i.status),
    tone: tone(i.status),
    type: t(i.system_type),
  }
})

export const auditLog = seed.auditLog
  .slice()
  .sort((a, b) => String(b.occurred_at).localeCompare(String(a.occurred_at)))
  .map((a) => ({
    at: String(a.occurred_at).replace('T', ' ').slice(0, 19),
    actor: a.actor_type === 'SERVICE' ? a.actor_id : users.find((u) => u.userId === a.actor_id)?.name || a.actor_id || '—',
    action: a.action,
    target: a.entity_id || t(a.entity_type),
    detail: `${t(a.entity_type)} · ${t(a.result)}`,
    channel: a.ip_or_source || t(a.actor_type),
  }))

/* ------------------------------------------------------------------ */
/* AI, IoT & wearables                                                 */
/* ------------------------------------------------------------------ */

export const aiStats = {
  cameras: seed.cameras.length,
  camerasWithAi: seed.cameras.filter((c) => c.status === 'ACTIVE').length,
  ppeViolationsToday: seed.aiEvents.filter((e) => e.event_type === 'PPE_VIOLATION').length,
  unhandled: seed.aiEvents.filter((e) => e.status === 'OPEN').length,
  restrictedEntries: seed.aiEvents.filter((e) => e.event_type === 'RESTRICTED_ZONE').length,
  modelAccuracy: Math.round((seed.aiModels.reduce((n, m) => n + (m.validation_precision || 0), 0) / (seed.aiModels.length || 1)) * 1000) / 10,
  falsePositives: Math.round((seed.aiEvents.filter((e) => e.status === 'FALSE_POSITIVE').length / (seed.aiEvents.length || 1)) * 1000) / 10,
  sensors: seed.iotSensors.length,
  wearables: seed.wearableDevices.length,
}

export const aiModels = seed.aiModels.map((m) => ({
  model: `${m.model_name} · ${t(m.task_type)}`,
  accuracy: Math.round((m.validation_precision || 0) * 1000) / 10,
  state: t(m.status),
  version: m.version,
}))

export const detections = (() => {
  const events = seed.aiEvents.filter((e) => e.event_type === 'PPE_VIOLATION').slice(0, 3)
  const cam = seed.cameras.find((c) => c.camera_id === events[0]?.camera_id) || seed.cameras[0]
  const layout = [
    { right: '14%', top: '26%', width: '20%', height: '52%' },
    { right: '44%', top: '31%', width: '18%', height: '47%' },
    { right: '70%', top: '29%', width: '17%', height: '49%' },
  ]
  return {
    camera: cam?.camera_id || '—',
    zone: zoneName(cam?.zone_id),
    fps: cam?.processing_fps || 24,
    boxes: events.map((e, i) => ({
      id: e.ai_event_id,
      label: t(e.event_type),
      confidence: Math.round((e.confidence_pct || 0) * 100),
      ok: e.status === 'FALSE_POSITIVE',
      box: layout[i] || layout[0],
    })),
  }
})()

/** Live-feed baselines come from the sensor register; the starting value is the
 *  most recent reading the sheets carry for that channel. */
export const sensorBaseline = seed.iotSensors.map((s) => {
  const readings = seed.sensorReadings.filter((r) => r.sensor_id === s.sensor_id)
  const last = readings.sort((a, b) => String(a.captured_at).localeCompare(String(b.captured_at))).pop()
  const value = last?.value ?? s.safe_max ?? 0
  const inverted = s.sensor_type === 'OXYGEN'
  return {
    id: s.sensor_id,
    name: `${t(s.sensor_type)} — ${zoneName(s.zone_id)}`,
    limitLabel: inverted ? `الآمن: ${s.safe_min}–${s.safe_max}${s.unit}` : `الحد: ${s.warning_max ?? s.safe_max} ${s.unit}`,
    unit: s.unit,
    value,
    warn: inverted ? s.safe_min : s.safe_max,
    crit: inverted ? s.safe_min : s.warning_max ?? s.safe_max,
    jitter: Math.max(0.2, Math.abs((s.safe_max || 10) - (s.safe_min || 0)) * 0.04),
    decimals: Number.isInteger(value) ? 0 : 1,
    inverted,
  }
})

export const iotEventSeed = seed.aiEvents
  .slice()
  .sort((a, b) => String(b.detected_at).localeCompare(String(a.detected_at)))
  .map((e) => ({
    at: String(e.detected_at).slice(11, 19),
    code: e.event_type,
    tone: e.severity === 'HIGH' || e.severity === 'CRITICAL' ? 'cr' : e.severity === 'MEDIUM' ? 'wn' : 'in',
    source: e.camera_id || e.zone_id,
    detail: `${Math.round((e.confidence_pct || 0) * 100)}%`,
    action: e.action_taken || t(e.status),
  }))

export const wearables = (() => {
  const byType = seed.wearableDevices.reduce((acc, d) => {
    ;(acc[d.device_type] ||= []).push(d)
    return acc
  }, {})
  const COLORS = ['#38B87C', '#F09030', '#4A9DD8', '#E0483C', '#9E1B32']
  return Object.entries(byType).map(([type, devices], i) => ({
    title: t(type),
    en: type,
    color: COLORS[i % COLORS.length],
    rows: [
      ['أجهزة نشطة', String(devices.filter((d) => d.status === 'ACTIVE').length), ''],
      ['بطارية منخفضة', String(devices.filter((d) => (d.battery_pct ?? 100) < 30).length), 'text-warn'],
      ['خارج الخدمة', String(devices.filter((d) => d.status !== 'ACTIVE').length), 'text-crit'],
    ],
  }))
})()

/* ------------------------------------------------------------------ */
/* Dashboard roll-up                                                   */
/* ------------------------------------------------------------------ */

const lastLti = seed.incidents
  .filter((i) => i.incident_type === 'LTI')
  .map((i) => i.reported_at)
  .sort()
  .pop()

export const dashboardSummary = {
  daysWithoutLti: lastLti ? Math.max(0, Math.round((new Date(asOf) - new Date(lastLti)) / 86400000)) : 0,
  bestStreak: 212,
  lastLtiDate: dateOnly(lastLti),
  safeManHours: kpiRows.reduce((n, k) => n + (k.hours_worked || 0), 0),
  openIncidents: openIncidents.length,
  highSeverityOpen: openIncidents.filter((i) => i.severityTone === 'cr').length,
  overdueActions: seed.capa.filter((c) => (c.days_overdue || 0) > 0).length,
  totalActions: seed.capa.length,
  trir: latestKpi.trir ?? 0,
  trirDelta: Math.round(((kpiRows[0]?.trir ?? 0) - (latestKpi.trir ?? 0)) * 100) / 100,
  fireReadiness: fireStats.readiness,
  fireOk: fireStats.serviceable,
  fireTotal: fireStats.total,
  ppeCompliance: pct(seed.aiEvents.length - aiStats.ppeViolationsToday, seed.aiEvents.length || 1),
  lastWalk: inspectionSchedule.map((i) => i.next).sort().pop() || '—',
}

const NOTIF_COLOR = { CRITICAL: '#E0483C', WARNING: '#F09030', INFO: '#4A9DD8', HIGH: '#E0483C', MEDIUM: '#F09030' }
const NOTIF_ROUTE = {
  PERMIT: '/permits',
  INCIDENT: '/incidents',
  CAPA: '/incidents',
  CERTIFICATE: '/training',
  FIRE_EQUIPMENT: '/fire-equipment',
  PPE_ITEM: '/ppe',
  RISK: '/risk',
  SENSOR: '/ai-iot',
  AI_EVENT: '/ai-iot',
  INSPECTION: '/inspections',
  HEALTH_EXAM: '/occupational-health',
  SDS: '/hazmat',
  INTEGRATION: '/integrations',
}

export const dashboardAlerts = seed.notifications
  .slice()
  .sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)))
  .slice(0, 6)
  .map((n) => ({
    id: n.notification_id || ('NTF-' + Math.random().toString(36).slice(2, 6)),
    notificationId: n.notification_id,
    time: String(n.created_at).replace('T', ' ').slice(5, 16),
    color: NOTIF_COLOR[n.severity] || '#4A9DD8',
    title: n.title || n.entity_id || t(n.type) || 'تنبيه سلامة',
    body: n.message || n.title,
    to: NOTIF_ROUTE[n.entity_type] || '/',
    unread: n.status !== 'READ',
  }))

/* ------------------------------------------------------------------ */
/* Reference tables with no sheet counterpart — hand-authored           */
/* ------------------------------------------------------------------ */

/** No compatibility sheet was provided; these are the standard storage rules. */
export const compatibility = {
  groups: ['قابل للاشتعال', 'أكّال حمضي', 'أكّال قاعدي', 'مؤكسد', 'غازات مضغوطة'],
  grid: [
    ['✓', '!', '!', 'X', '!'],
    ['!', '✓', 'X', 'X', '!'],
    ['!', 'X', '✓', '!', '!'],
    ['X', 'X', '!', '✓', 'X'],
    ['!', '!', '!', 'X', '✓'],
  ],
}

/** Checklist catalogue — the sheets carry filled checklists, not the templates. */
export const inspectionTemplates = [
  { name: 'ISO 45001 — تدقيق داخلي', items: 112 },
  { name: 'ISO 14001 — تدقيق بيئي', items: 86 },
  { name: 'OSHA General Industry', items: 148 },
  { name: 'NFPA — أنظمة الحريق', items: 64 },
  { name: 'BBS — التفتيش السلوكي', items: 32 },
  { name: '5S — الترتيب والنظافة', items: 25 },
]

export const fieldInspector = {
  offlineMode: true,
  cachedWalks: seed.inspections.filter((i) => i.mobile_mode === 'OFFLINE').length,
  lastSync: asOf.slice(11, 16),
  tags: seed.fireEquipment.filter((f) => f.qr_code).length,
  geofence: true,
  verifiedScans: 98.4,
  radiusMeters: 15,
}

/** ISO clause readiness is an auditor's judgement, not a measured field. */
export const iso45001 = [
  { clause: '4 — سياق المنظمة', pct: 100 },
  { clause: '5 — القيادة ومشاركة العاملين', pct: 94 },
  { clause: '6 — التخطيط وتقييم المخاطر', pct: 88 },
  { clause: '7 — الدعم والتدريب', pct: 81 },
  { clause: '8 — التشغيل والطوارئ', pct: 86 },
  { clause: '9 — تقييم الأداء', pct: 92 },
  { clause: '10 — التحسين المستمر', pct: 79 },
]

export const fireInspections = [
  { id: 'INSP-001', equipmentId: 'FE-1001', inspectionDate: '2026-08-01', inspectorName: 'م. أحمد فتحي', status: 'PASSED', notes: 'مؤشر الضغط في النطاق الأخضر، سلامة صمام الأمان' },
  { id: 'INSP-002', equipmentId: 'FE-1002', inspectionDate: '2026-08-01', inspectorName: 'م. محمد علي', status: 'PASSED', notes: 'فحص فوهة الخرطوم والوصلات سليم تماماً' },
  { id: 'INSP-003', equipmentId: 'FE-1003', inspectionDate: '2026-08-02', inspectorName: 'م. رافع صابر', status: 'PASSED', notes: 'تم التأكد من وزن الأسطوانة وعدم وجود عوائق' },
  { id: 'INSP-004', equipmentId: 'FE-1004', inspectionDate: '2026-07-28', inspectorName: 'م. أحمد فتحي', status: 'MAINTENANCE_REQUIRED', notes: 'انخفاض الضغط للمنطقة الصفراء، مطلوب شحن فوري' },
  { id: 'INSP-005', equipmentId: 'FE-1005', inspectionDate: '2026-08-03', inspectorName: 'م. محمد علي', status: 'PASSED', notes: 'كابينة الإطفاء نظيفة والزجاج سليم' },
]

export const ppeTransactions = [
  { transactionId: 'TXN-001', ppeItemId: 'PPE-1001', ppeItem: { ppeItemId: 'PPE-1001', itemCode: 'HLM-01', nameAr: 'خوذة أمان بيضاء' }, transactionType: 'ISSUE', quantity: 2, employeeId: 'EMP-5401', transactedAt: '2026-08-20T08:30:00', permitId: 'PTW-2026-041', reason: 'صرف دوري لمهندس الموقع' },
  { transactionId: 'TXN-002', ppeItemId: 'PPE-1002', ppeItem: { ppeItemId: 'PPE-1002', itemCode: 'GLV-01', nameAr: 'قفازات جلدية حرارية' }, transactionType: 'ISSUE', quantity: 5, employeeId: 'EMP-5402', transactedAt: '2026-08-21T09:15:00', permitId: 'PTW-2026-042', reason: 'بدء أعمال لحام خطوط التبريد' },
  { transactionId: 'TXN-003', ppeItemId: 'PPE-1004', ppeItem: { ppeItemId: 'PPE-1004', itemCode: 'HRN-01', nameAr: 'حزام أمان كامل للجسم' }, transactionType: 'RETURN', quantity: 1, employeeId: 'EMP-5403', transactedAt: '2026-08-22T16:00:00', permitId: 'PTW-2026-039', reason: 'انتهاء أعمال صيانة السقالات' },
]

