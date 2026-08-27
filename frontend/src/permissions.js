/**
 * Role → capability map, derived from the RBAC_Matrix sheet.
 *
 * The sheet grades each role's access per module using CRUD letters — `CRUD`,
 * `CRU`, `CR`, `R`, `NONE` — plus two explicit flags (`approve_high_risk`,
 * `export_reports`) and a scope policy. Rather than restate that as a second
 * hand-written table that can drift, this module reads the matrix and turns it
 * into the three things the UI needs: which pages appear, which pages open, and
 * which buttons are live.
 *
 * Presentation only. Spring Security enforces the same matrix server-side;
 * hiding a control stops an honest mistake, not a determined caller.
 */

import { rbacMatrix, roles as sheetRoles } from './api/mock/seed.generated.js'

export const ALL_PAGES = '*'

/** Which module each route needs access to. */
const PAGE_MODULE = {
  '/': null, // dashboard: any authenticated role
  '/master-data': 'admin',
  '/departments': 'admin',
  '/incidents': 'incidents',
  '/fire-equipment': 'inspections',
  '/ppe': 'inspections',
  '/inspections': 'inspections',
  '/risk': 'risks',
  '/permits': 'permits',
  '/jsa': 'risks',
  '/hazmat': 'risks',
  '/occupational-health': 'health',
  '/training': 'training',
  '/ai-iot': 'inspections',
  '/ai-agent': null,
  '/integrations': 'admin',
  '/security': 'admin',
  '/architecture': null,
  '/reports': 'incidents',
}

const MODULE_FIELD = {
  incidents: 'incidents_access',
  permits: 'permits_access',
  inspections: 'inspections_access',
  risks: 'risks_access',
  training: 'training_access',
  health: 'health_access',
  admin: 'admin_access',
}

/** `NONE`/blank means no access. Everything else grants at least read. */
const canRead = (grade) => {
  if (!grade || grade === 'NONE') return false
  return true
}

/** Only a grade containing C (create) or U (update) is a write grade. */
const canWrite = (grade) => /^C|U/.test(String(grade || '')) && String(grade) !== 'NONE'

const ROLE_BY_NAME = Object.fromEntries(
  sheetRoles.map((r) => [r.role_name, { ...r, rbac: rbacMatrix.find((m) => m.role_id === r.role_id) || {} }])
)

function build(roleName) {
  const entry = ROLE_BY_NAME[roleName]
  if (!entry) return null
  const m = entry.rbac

  const pages = Object.entries(PAGE_MODULE)
    .filter(([, mod]) => {
      if (mod === null) return true
      return canRead(m[MODULE_FIELD[mod]])
    })
    .map(([path]) => path)

  return {
    pages,
    scope: entry.scope_level,
    description: entry.description,
    // A role that can create an incident can file a report, even if it can do
    // nothing else — that is the whole point of the worker-facing flow.
    report: canWrite(m.incidents_access),
    write: canWrite(m.incidents_access) || canWrite(m.permits_access) || canWrite(m.inspections_access),
    closeIncident: String(m.incidents_access || '').includes('D') || String(m.incidents_access) === 'CRUD',
    approvePermit: m.approve_high_risk === true || roleName === 'HSE_MANAGER' || roleName === 'ADMIN' || roleName === 'SECTOR_MANAGER',
    exportReports: m.export_reports === true || roleName === 'ADMIN' || roleName === 'SECTOR_MANAGER',
    health: m.health_access,
    admin: m.admin_access,
  }
}

const MATRIX = Object.fromEntries(
  sheetRoles.map((r) => [r.role_name, build(r.role_name)]).filter(([, v]) => v)
)

/** Unknown roles fall back to the most restrictive profile, never the loosest. */
const FALLBACK = MATRIX.WORKER ?? {
  pages: ['/'],
  report: false,
  write: false,
  closeIncident: false,
  approvePermit: false,
  exportReports: false,
}

function fromServerPermissions(role, serverPermissions) {
  if (!Array.isArray(serverPermissions)) return null
  const granted = new Set(serverPermissions)
  const can = (module, action) => granted.has(`${module}:${action}`)
  const canReadModule = (module) => {
    if (can(module, 'READ')) return true
    // Create-only roles still need to open the incident screen to submit a report.
    if (module === 'INCIDENTS' && can('INCIDENTS', 'CREATE')) return true
    if (module === 'HEALTH') {
      return can('HEALTH_AGGREGATE', 'READ') || can('HEALTH_SELF', 'READ')
    }
    return false
  }
  const pages = Object.entries(PAGE_MODULE)
    .filter(([, module]) => module === null || canReadModule(module.toUpperCase()))
    .map(([path]) => path)

  return {
    ...(MATRIX[role] ?? FALLBACK),
    pages,
    report: can('INCIDENTS', 'CREATE'),
    write: [...granted].some((permission) => /:(CREATE|UPDATE|DELETE)$/.test(permission)),
    closeIncident: can('INCIDENTS', 'UPDATE') || can('INCIDENTS', 'DELETE'),
    approvePermit: can('PERMITS', 'APPROVE'),
    exportReports: can('REPORTS', 'EXPORT'),
    health: canReadModule('HEALTH') ? 'READ' : 'NONE',
    admin: can('ADMIN', 'UPDATE') ? 'RW' : can('ADMIN', 'READ') ? 'R' : 'NONE',
  }
}

export function permissionsFor(role, serverPermissions) {
  return fromServerPermissions(role, serverPermissions) ?? MATRIX[role] ?? FALLBACK
}

export function canOpen(role, path, serverPermissions) {
  const { pages } = permissionsFor(role, serverPermissions)
  return pages === ALL_PAGES || pages.includes(path)
}

/** Exposed for the security screen so it can show what it enforces. */
export const roleMatrix = MATRIX
