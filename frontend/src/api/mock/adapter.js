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

let dynamicPermits = [...(db.permits || [])]
let dynamicInspectionSchedule = [...(db.inspectionSchedule || [])]
let dynamicInspectionFindings = [...(db.inspectionFindings || [])]
let dynamicTrainingSchedule = [...(db.trainingSchedule || [
  { id: 'TRN-001', certId: 1, employee: 'محمود عبد الله', dept: 'خط الإنتاج A', course: 'السلامة العامة (General Induction)', provider: 'ESCA HSE Academy', issueDate: '2025-01-15', expiryDate: '2026-12-15', evidenceRef: 'CERT-2026-0001', status: 'سارية ومعتمدة', statusTone: 'ok' },
  { id: 'TRN-002', certId: 2, employee: 'هبة فؤاد', dept: 'خط الإنتاج B', course: 'العمل الساخن (Hot Work)', provider: 'Elsewedy Technical Training Center', issueDate: '2025-03-01', expiryDate: '2027-01-04', evidenceRef: 'CERT-2026-0002', status: 'سارية ومعتمدة', statusTone: 'ok' },
  { id: 'TRN-003', certId: 3, employee: 'أحمد سامي', dept: 'ورشة الصيانة الميكانيكية', course: 'القفل وتطبيق بطاقة LOTO', provider: 'External Certified Provider', issueDate: '2025-04-15', expiryDate: '2027-01-24', evidenceRef: 'CERT-2026-0003', status: 'سارية ومعتمدة', statusTone: 'ok' },
  { id: 'TRN-004', certId: 4, employee: 'كريم رشاد', dept: 'المخازن والخام', course: 'العمل على ارتفاع (Working at Height)', provider: 'ESCA HSE Academy', issueDate: '2025-05-30', expiryDate: '2027-02-13', evidenceRef: 'CERT-2026-0004', status: 'مجدولة للتجديد', statusTone: 'wn' },
])]
let dynamicTrainingExpiring = [...(db.trainingExpiring || [])]
let dynamicHealthSchedule = [...(db.healthSchedule || [
  { id: 'HEX-001', employee: 'محمود عبد الله', protocol: 'فحص قياس السمع (Audiometry)', scheduledDate: '2026-08-28', completedDate: '2026-08-28', fitness: 'لائق طبياً', fitnessTone: 'ok', restrictions: 'لا توجد قيود', doctor: 'د. حازم القاضي', nextDueDate: '2027-02-28', status: 'مكتمل', statusTone: 'ok' },
  { id: 'HEX-002', employee: 'هبة فؤاد', protocol: 'فحص وظائف التنفس والرئة (Spirometry)', scheduledDate: '2026-08-29', completedDate: null, fitness: 'قيد الانتظار', fitnessTone: 'wn', restrictions: 'تحت التقييم', doctor: 'د. سمر الشافعي', nextDueDate: '2027-02-28', status: 'مجدول', statusTone: 'in' },
  { id: 'HEX-003', employee: 'أحمد سامي', protocol: 'لياقة الارتفاعات والأماكن المغلقة', scheduledDate: '2026-08-30', completedDate: '2026-08-30', fitness: 'لائق مع قيود', fitnessTone: 'wn', restrictions: 'تجنب العمل على ارتفاعات > 10م', doctor: 'د. حازم القاضي', nextDueDate: '2026-11-30', status: 'مكتمل', statusTone: 'ok' },
])]
let dynamicAlerts = [...(db.dashboardAlerts || [
  { id: 'NTF-001', title: 'انتهاء صلاحية تصريح عمل ePTW', body: 'تصريح العمل الساخن رقم PERM-104 في خط الكابلات A تجاوز موعد انتهائه.', time: 'منذ 10 دقائق', color: 'var(--crit)', to: '/permits', unread: true },
  { id: 'NTF-002', title: 'تنبيه فحص طفاية حريق دوري', body: 'طفاية حريق CO2 بمبنى الإدارة (FE-012) مستحقة للفحص الهيدروستاتيكي.', time: 'منذ 30 دقيقة', color: 'var(--warn)', to: '/fire-equipment', unread: true },
  { id: 'NTF-003', title: 'إجراء تصحيحي CAPA متأخر', body: 'إجراء تركيب حاجز حماية على ماكينة الجدل تجاوز الموعد المستهدف.', time: 'منذ ساعتين', color: 'var(--warn)', to: '/incidents', unread: true },
])]

let dynamicJsaList = [
  { id: 'JSA-001', numericId: 1, jsaId: 1, task: 'أعمال لحام وقطع في مسار الكابلات الرئيسي', taskName: 'أعمال لحام وقطع في مسار الكابلات الرئيسي', zone: 'خطوط العزل CCV', zoneId: 1, steps: 4, criticalSteps: 2, permitType: 'HOT_WORK', linkedPermit: 'عمل ساخن (PTW-001)', linkedPermitId: 1, permitRequired: true, reviewed: '2026-08-01', status: 'معتمد', rawStatus: 'APPROVED', statusId: 3, tone: 'ok', inherentScore: 16, residualScore: 4 },
  { id: 'JSA-002', numericId: 2, jsaId: 2, task: 'استبدال كابل التغذية وقواطع الجهد المتوسط 11kV', taskName: 'استبدال كابل التغذية وقواطع الجهد المتوسط 11kV', zone: 'محطة المحولات الرئيسية', zoneId: 7, steps: 3, criticalSteps: 2, permitType: 'ELECTRICAL', linkedPermit: 'كهربائي (PTW-002)', linkedPermitId: 2, permitRequired: true, reviewed: '2026-07-15', status: 'معتمد', rawStatus: 'APPROVED', statusId: 3, tone: 'ok', inherentScore: 20, residualScore: 5 },
  { id: 'JSA-003', numericId: 3, jsaId: 3, task: 'صيانة الإنارة العلوية بالسقالات المتحركة', taskName: 'صيانة الإنارة العلوية بالسقالات المتحركة', zone: 'المستودع الرئيسي', zoneId: 4, steps: 3, criticalSteps: 1, permitType: 'WORK_AT_HEIGHT', linkedPermit: 'مرتفعات (PTW-003)', linkedPermitId: 3, permitRequired: true, reviewed: '2026-06-20', status: 'معتمد', rawStatus: 'APPROVED', statusId: 3, tone: 'ok', inherentScore: 12, residualScore: 4 },
  { id: 'JSA-004', numericId: 4, jsaId: 4, task: 'تفتيش وتنظيف خزان مياه التبريد المركزي', taskName: 'تفتيش وتنظيف خزان مياه التبريد المركزي', zone: 'محطة التبريد المركزي', zoneId: 6, steps: 3, criticalSteps: 2, permitType: 'CONFINED_SPACE', linkedPermit: 'أماكن مغلقة (PTW-004)', linkedPermitId: 4, permitRequired: true, reviewed: '2026-08-10', status: 'معتمد', rawStatus: 'APPROVED', statusId: 3, tone: 'ok', inherentScore: 20, residualScore: 5 },
  { id: 'JSA-005', numericId: 5, jsaId: 5, task: 'استبدال رولمان بلي وسير محرك خط الجدل 61 سلك', taskName: 'استبدال رولمان بلي وسير محرك خط الجدل 61 سلك', zone: 'عنبر السحب والجدل', zoneId: 2, steps: 2, criticalSteps: 1, permitType: 'MECHANICAL_LOTO', linkedPermit: 'ميكانيكي / LOTO (PTW-005)', linkedPermitId: 5, permitRequired: true, reviewed: '2026-08-12', status: 'معتمد', rawStatus: 'APPROVED', statusId: 3, tone: 'ok', inherentScore: 15, residualScore: 4 },
]

let dynamicJsaSteps = {
  'JSA-001': [
    { id: 1, stepId: 1, stepNo: 1, step: 'فحص ومعايرة أجهزة قياس الغازات والأكسجين', hazard: 'تراكم غازات قابلة للاشتعال', control: 'قياس مسبق بنسبة لا تتجاوز 0% LEL ونسبة أكسجين 19.5%–23.5%', before: 16, after: 4, responsible: 'مسؤول السلامة' },
    { id: 2, stepId: 2, stepNo: 2, step: 'إخلاء محيط 10 أمتار من المواد القابلة للاحتراق', hazard: 'تطاير الشرر واشتعال المواد البوليمرية', control: 'فرش أغطية مقاومة للحريق وتوفير مطافئ بودرة كيميائية', before: 16, after: 4, responsible: 'مراقب الحريق' },
    { id: 3, stepId: 3, stepNo: 3, step: 'تعيين مراقب حريق مخصص (Fire Watch)', hazard: 'نشوب حريق غير مرئي', control: 'تواجد مراقب الحريق طوال فترة العمل ولمدة 60 دقيقة بعد الانتهاء', before: 15, after: 3, responsible: 'مراقب الحريق' },
    { id: 4, stepId: 4, stepNo: 4, step: 'عزل مصادر الطاقة الكهربائية وتطبيق LOTO', hazard: 'صعق كهربائي وتشغيل مفاجئ', control: 'وضع أقفال وبطاقات تحذيرية والتأكد من انعدام الجهد', before: 20, after: 4, responsible: 'فريق الصيانة الكهربائية' }
  ],
  'JSA-002': [
    { id: 5, stepId: 5, stepNo: 1, step: 'فصل وتأمين المفاتيح الرئيسية وتفريغ الشحنات', hazard: 'جهد متبقي وقوس كهربائي', control: 'تأريض تفريغ معتمد وارتداء قفازات 11kV', before: 20, after: 5, responsible: 'مهندس الكهرباء' },
    { id: 6, stepId: 6, stepNo: 2, step: 'اختبار انعدام الجهد بواسطة جهاز كشف معتمد', hazard: 'صعق كهربائي مميت', control: 'فحص ثلاثي الأطوار وتطبيق بطاقة LOTO', before: 20, after: 4, responsible: 'فني الكهرباء' }
  ],
  'JSA-003': [
    { id: 7, stepId: 7, stepNo: 1, step: 'فحص سلامة وتثبيت السقالة المتحركة وقفل العجلات', hazard: 'انزلاق السقالة أو عدم استقرارها', control: 'تثبيت فرامل العجلات وفحص كارت تصريح السقالات الأخضر', before: 15, after: 4, responsible: 'مشرف السقالات' },
    { id: 8, stepId: 8, stepNo: 2, step: 'ارتداء حزام الأمان وتثبيت حبل النجاة', hazard: 'سقوط العامل من ارتفاع', control: 'ربط حبل النجاة في نقطة تثبيت معتمدة > 22kN', before: 16, after: 3, responsible: 'فني الصيانة' }
  ]
}

let dynamicChemicals = [
  { id: 41, chemicalId: 41, code: 'CHM-041', name: 'صوديوم بنتا أوكسايد (Sodium Pentaoxide)', tradeName: 'صوديوم بنتا أوكسايد (Sodium Pentaoxide)', chemicalName: 'Sodium Pentaoxide (Na2O5)', cas: '12034-11-6', casNumber: '12034-11-6', supplier: 'Elsewedy Chemical Supply', quantity: 50.0, unit: 'KG', qty: '50 KG', ghsClasses: 'OXIDIZER', ghs: 'GHS03 مادة مؤكسدة', tone: 'crit', class: 'Class 5.1', storageClass: 'Class 5.1 Oxidizer', zoneId: 9, location: 'مخزن المواد الكيميائية الرئيسي', status: 'ACTIVE', statusId: 1, statusAr: 'نشط ومصرح به', sds: '2027-01', sdsId: 6, sdsVersion: 'Rev 1', sdsExpiryDate: '2027-01-10', sdsStatus: 'CURRENT', fileRef: 'SDS-ESCA-041.pdf', emergencySummary: 'مادة مؤكسدة وأكالة — عزل المصدر واستخدام قناع واقي وقفازات مطاطية مقاومة.' },
  { id: 1, chemicalId: 1, code: 'CHM-001', name: 'DURACLEAN 200', tradeName: 'DURACLEAN 200', chemicalName: 'Alkaline Cleaner', cas: '1310-73-2', casNumber: '1310-73-2', supplier: 'EgyChem', quantity: 180.0, unit: 'L', qty: '180 L', ghsClasses: 'CORROSIVE', ghs: 'GHS05 مادة أكالة', tone: 'warn', class: 'Class 8', storageClass: 'Class 8', zoneId: 9, location: 'مخزن المواد الكيميائية', status: 'ACTIVE', statusId: 1, statusAr: 'نشط ومصرح به', sds: '2027-01', sdsId: 1, sdsVersion: 'Rev 1', sdsExpiryDate: '2027-01-10', sdsStatus: 'CURRENT', fileRef: 'SDS-ESCA-001.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.' },
  { id: 2, chemicalId: 2, code: 'CHM-002', name: 'WELD-ANTI SP', tradeName: 'WELD-ANTI SP', chemicalName: 'Anti-Spatter Compound', cas: '9003-39-8', casNumber: '9003-39-8', supplier: 'Nile Chemicals', quantity: 75.0, unit: 'kg', qty: '75 kg', ghsClasses: 'IRRITANT', ghs: 'GHS07 مخرش / تنبيه', tone: 'wn', class: 'Class 8', storageClass: 'Class 8', zoneId: 9, location: 'مخزن المواد الكيميائية', status: 'ACTIVE', statusId: 1, statusAr: 'نشط ومصرح به', sds: '2027-01', sdsId: 2, sdsVersion: 'Rev 2', sdsExpiryDate: '2027-01-30', sdsStatus: 'CURRENT', fileRef: 'SDS-ESCA-002.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.' },
  { id: 3, chemicalId: 3, code: 'CHM-003', name: 'CUTSAFE 46', tradeName: 'CUTSAFE 46', chemicalName: 'Hydraulic Oil', cas: '64742-54-7', casNumber: '64742-54-7', supplier: 'Delta Industrial', quantity: 240.0, unit: 'L', qty: '240 L', ghsClasses: 'ASPIRATION_HAZARD', ghs: 'GHS08 خطر صحي', tone: 'warn', class: 'Class 3', storageClass: 'Class 3', zoneId: 9, location: 'مخزن المواد الكيميائية', status: 'ACTIVE', statusId: 1, statusAr: 'نشط ومصرح به', sds: '2027-02', sdsId: 3, sdsVersion: 'Rev 3', sdsExpiryDate: '2027-02-19', sdsStatus: 'CURRENT', fileRef: 'SDS-ESCA-003.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.' },
  { id: 4, chemicalId: 4, code: 'CHM-004', name: 'SOLV-IPA', tradeName: 'SOLV-IPA', chemicalName: 'Isopropyl Alcohol', cas: '67-63-0', casNumber: '67-63-0', supplier: 'Alexandria Chemical', quantity: 120.0, unit: 'L', qty: '120 L', ghsClasses: 'FLAMMABLE', ghs: 'GHS02 سريع الاشتعال', tone: 'crit', class: 'Class 3', storageClass: 'Class 3', zoneId: 9, location: 'مخزن المواد الكيميائية', status: 'ACTIVE', statusId: 1, statusAr: 'نشط ومصرح به', sds: '2027-03', sdsId: 4, sdsVersion: 'Rev 1', sdsExpiryDate: '2027-03-11', sdsStatus: 'DUE_SOON', fileRef: 'SDS-ESCA-004.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.' },
  { id: 5, chemicalId: 5, code: 'CHM-005', name: 'PAINT THINNER', tradeName: 'PAINT THINNER', chemicalName: 'Organic Solvent', cas: '64742-89-8', casNumber: '64742-89-8', supplier: 'EgyChem', quantity: 90.0, unit: 'L', qty: '90 L', ghsClasses: 'FLAMMABLE', ghs: 'GHS02 سريع الاشتعال', tone: 'crit', class: 'Class 3', storageClass: 'Class 3', zoneId: 9, location: 'مخزن المواد الكيميائية', status: 'PHASED_OUT', statusId: 2, statusAr: 'تم التخلص التدريجي', sds: '2027-03', sdsId: 5, sdsVersion: 'Rev 2', sdsExpiryDate: '2027-03-31', sdsStatus: 'CURRENT', fileRef: 'SDS-ESCA-005.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.' },
]

let dynamicSdsList = [
  { sdsId: 1, id: 1, chemicalId: 1, chemicalCode: 'CHM-001', tradeName: 'DURACLEAN 200', chemicalName: 'Alkaline Cleaner', casNumber: '1310-73-2', supplier: 'EgyChem', versionNo: 'Rev 1', version: 'Rev 1', issueDate: '2025-01-10', expiryDate: '2027-01-10', language: 'EN/AR', fileRef: 'SDS-ESCA-001.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.', status: 'CURRENT', statusAr: 'سارية ومحدثة', daysToExpiry: 143, isExpired: false, isDueSoon: false, tone: 'safe' },
  { sdsId: 2, id: 2, chemicalId: 2, chemicalCode: 'CHM-002', tradeName: 'WELD-ANTI SP', chemicalName: 'Anti-Spatter Compound', casNumber: '9003-39-8', supplier: 'Nile Chemicals', versionNo: 'Rev 2', version: 'Rev 2', issueDate: '2025-02-14', expiryDate: '2027-01-30', language: 'EN/AR', fileRef: 'SDS-ESCA-002.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.', status: 'CURRENT', statusAr: 'سارية ومحدثة', daysToExpiry: 155, isExpired: false, isDueSoon: false, tone: 'safe' },
  { sdsId: 3, id: 3, chemicalId: 3, chemicalCode: 'CHM-003', tradeName: 'CUTSAFE 46', chemicalName: 'Hydraulic Oil', casNumber: '64742-54-7', supplier: 'Delta Industrial', versionNo: 'Rev 3', version: 'Rev 3', issueDate: '2025-03-21', expiryDate: '2027-02-19', language: 'EN/AR', fileRef: 'SDS-ESCA-003.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.', status: 'CURRENT', statusAr: 'سارية ومحدثة', daysToExpiry: 167, isExpired: false, isDueSoon: false, tone: 'safe' },
  { sdsId: 4, id: 4, chemicalId: 4, chemicalCode: 'CHM-004', tradeName: 'SOLV-IPA', chemicalName: 'Isopropyl Alcohol', casNumber: '67-63-0', supplier: 'Alexandria Chemical', versionNo: 'Rev 1', version: 'Rev 1', issueDate: '2025-04-25', expiryDate: '2027-03-11', language: 'EN/AR', fileRef: 'SDS-ESCA-004.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.', status: 'DUE_SOON', statusAr: 'تقترب من الانتهاء', daysToExpiry: 85, isExpired: false, isDueSoon: true, tone: 'wn' },
  { sdsId: 5, id: 5, chemicalId: 5, chemicalCode: 'CHM-005', tradeName: 'PAINT THINNER', chemicalName: 'Organic Solvent', casNumber: '64742-89-8', supplier: 'EgyChem', versionNo: 'Rev 2', version: 'Rev 2', issueDate: '2025-05-30', expiryDate: '2027-03-31', language: 'EN/AR', fileRef: 'SDS-ESCA-005.pdf', emergencySummary: 'Isolate source, use required PPE, ventilate the area and contact HSE for spill or exposure response.', status: 'CURRENT', statusAr: 'سارية ومحدثة', daysToExpiry: 191, isExpired: false, isDueSoon: false, tone: 'safe' },
]

/* ---------------- route table ---------------- */
/* [method, path pattern, handler(params, query, body)] */

/**
 * Automation rule: scan all training certificates and mark expired ones,
 * injecting a live alert into dynamicAlerts if not already present.
 * Called on every notification/dashboard/training fetch and automation trigger.
 */
function evaluateCertificateExpirations() {
  const now = new Date()
  dynamicTrainingSchedule = dynamicTrainingSchedule.map((item) => {
    if (item.status && item.status.includes('منتهية')) return item

    const expDate = item.expiryDate || '2099-12-31'
    let expTime = item.expiryTime || ''
    if (!expTime && item.evidenceRef && item.evidenceRef.includes('@')) {
      expTime = item.evidenceRef.split('@')[1].trim()
    }
    if (!expTime) expTime = '23:59'
    const targetDt = new Date(`${expDate}T${expTime.length === 5 ? expTime + ':00' : expTime}`)

    if (!isNaN(targetDt.getTime()) && targetDt <= now) {
      const updatedItem = {
        ...item,
        status: 'منتهية الصلاحية (EXPIRED)',
        statusTone: 'cr',
      }

      const alreadyAlerted = dynamicAlerts.some(
        (a) =>
          a.type === 'AUTOMATION_CERTIFICATE_EXPIRY' &&
          a.body &&
          a.body.includes(item.employee) &&
          a.body.includes(item.course)
      )
      if (!alreadyAlerted) {
        const alertItem = {
          id: 'NTF-' + Date.now() + '-' + Math.floor(Math.random() * 1000),
          notificationId: Date.now(),
          title: `تنبيه أتمتة السلامة: انتهاء صلاحية شهادة ${item.employee}`,
          body: `انتهت صلاحية شهادة تدريب الموظف ${item.employee} لدورة (${item.course}) في ${item.fullExpiry || expDate} — تم تفعيل تنبيه السلامة الآلي (AUT-002).`,
          time: 'الآن (مباشر)',
          color: 'var(--crit)',
          type: 'AUTOMATION_CERTIFICATE_EXPIRY',
          to: '/training',
          unread: true,
        }
        dynamicAlerts = [alertItem, ...dynamicAlerts]
      }
      return updatedItem
    }
    return item
  })
}

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

  ['get', '/users/me', () => {
    const user = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
    return {
      userId: user.id || user.user_id || 'USR-000',
      employeeId: user.employeeId || 'EMP-001',
      username: user.username || 'mostafa',
      fullName: user.displayName || user.name || user.fullName || 'مصطفى محمد',
      email: user.email || 'mostafa@elsewedy.com',
      phone: user.phone || '01000000001',
      jobTitle: user.roleLabel || user.roleAr || 'مدير السلامة والصحة المهنية (HSE Manager)',
      zoneName: user.zone || user.zoneName || 'خطوط العزل CCV',
      departmentName: user.department || user.departmentName || 'قطاع الإنتاج والتصنيع (ESCA)',
      avatarPath: user.avatarPath || user.avatar_path || null,
    }
  }],
  ['patch', '/users/me', (_p, _q, body) => {
    const user = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
    const next = {
      ...user,
      username: body?.username || user.username || 'mostafa',
      displayName: body?.fullName || user.displayName || 'مصطفى محمد',
      name: body?.fullName || user.name || 'مصطفى محمد',
      fullName: body?.fullName || user.fullName || 'مصطفى محمد',
    }
    localStorage.setItem('esca.hse.user', JSON.stringify(next))
    return {
      userId: next.id || next.user_id || 'USR-000',
      employeeId: next.employeeId || 'EMP-001',
      username: next.username,
      fullName: next.fullName || next.displayName || next.name,
      email: next.email || 'mostafa@elsewedy.com',
      phone: next.phone || '01000000001',
      jobTitle: next.roleLabel || next.roleAr || 'مدير السلامة والصحة المهنية (HSE Manager)',
      zoneName: next.zone || next.zoneName || 'خطوط العزل CCV',
      departmentName: next.department || next.departmentName || 'قطاع الإنتاج والتصنيع (ESCA)',
      avatarPath: next.avatarPath || next.avatar_path || null,
    }
  }],
  ['post', '/users/me/avatar', async (_p, _q, body) => {
    const user = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
    let avatarUrl = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80'
    if (body instanceof FormData) {
      const file = body.get('avatar')
      if (file && typeof file === 'object' && file.size) {
        try {
          avatarUrl = await new Promise((res) => {
            const reader = new FileReader()
            reader.onload = () => res(reader.result)
            reader.onerror = () => res(avatarUrl)
            reader.readAsDataURL(file)
          })
        } catch { }
      }
    }
    const next = { ...user, avatarPath: avatarUrl }
    localStorage.setItem('esca.hse.user', JSON.stringify(next))
    return {
      userId: next.id || next.user_id || 'USR-000',
      employeeId: next.employeeId || 'EMP-001',
      username: next.username || 'mostafa',
      fullName: next.displayName || next.name || 'مصطفى محمد',
      email: next.email || 'mostafa@elsewedy.com',
      phone: next.phone || '01000000001',
      jobTitle: next.roleLabel || next.roleAr || 'مدير السلامة والصحة المهنية (HSE Manager)',
      zoneName: next.zone || 'خطوط العزل CCV',
      departmentName: next.department || 'قطاع الإنتاج والتصنيع (ESCA)',
      avatarPath: avatarUrl,
    }
  }],
  ['delete', '/users/me/avatar', () => {
    const user = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
    const next = { ...user, avatarPath: null }
    localStorage.setItem('esca.hse.user', JSON.stringify(next))
    return {
      userId: next.id || next.user_id || 'USR-000',
      employeeId: next.employeeId || 'EMP-001',
      username: next.username || 'mostafa',
      fullName: next.displayName || next.name || 'مصطفى محمد',
      email: next.email || 'mostafa@elsewedy.com',
      phone: next.phone || '01000000001',
      jobTitle: next.roleLabel || next.roleAr || 'مدير السلامة والصحة المهنية (HSE Manager)',
      zoneName: next.zone || 'خطوط العزل CCV',
      departmentName: next.department || 'قطاع الإنتاج والتصنيع (ESCA)',
      avatarPath: null,
    }
  }],
  ['post', '/users/me/password/mfa/request', () => ({ codeSent: true, expiresInSeconds: 120, developmentCode: '749201' })],
  ['post', '/users/me/password/mfa/verify', () => null],
  ['post', '/users/me/email/mfa/request', () => ({ codeSent: true, expiresInSeconds: 120, developmentCode: '839102' })],
  ['post', '/users/me/email/mfa/verify', (_p, _q, body) => {
    const user = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
    const next = { ...user, email: body?.newEmail || user.email }
    localStorage.setItem('esca.hse.user', JSON.stringify(next))
    return {
      userId: next.id || next.user_id || 'USR-000',
      employeeId: next.employeeId || 'EMP-001',
      username: next.username || 'mostafa',
      fullName: next.displayName || next.name || 'مصطفى محمد',
      email: next.email,
      phone: next.phone || '01000000001',
      jobTitle: next.roleLabel || next.roleAr || 'مدير السلامة والصحة المهنية (HSE Manager)',
      zoneName: next.zone || 'خطوط العزل CCV',
      departmentName: next.department || 'قطاع الإنتاج والتصنيع (ESCA)',
      avatarPath: next.avatarPath || null,
    }
  }],


  /* master data — the reference-data coverage sheet */
  ['get', '/master-data/summary', () => ({
    ...db.masterSummary,
    sheets: db.sheetMeta,
    departments: db.departments.flatMap((s) => s.zones),
    zoneCount: db.departments.reduce((n, s) => n + s.zones.reduce((m, z) => m + z.zoneCount, 0), 0),
  })],

  /* dashboard & notifications */
  ['get', '/dashboard/summary', () => db.dashboardSummary],
  ['get', '/dashboard/safety-score', () => db.safetyByZone],
  ['get', '/dashboard/alerts', () => {
    evaluateCertificateExpirations()
    return [...dynamicAlerts]
  }],
  ['get', '/notifications', () => {
    evaluateCertificateExpirations()
    return [...dynamicAlerts]
  }],
  ['get', '/api/v1/notifications', () => {
    evaluateCertificateExpirations()
    return [...dynamicAlerts]
  }],
  ['post', '/notifications/mark-read', (_p, _q, body) => {
    const nid = body?.notificationId || body?.id
    dynamicAlerts = dynamicAlerts.map((a) =>
      a.id === nid || a.notificationId === nid || String(a.id) === String(nid) ? { ...a, unread: false } : a
    )
    return { ok: true, success: true }
  }],
  ['post', '/api/v1/notifications/mark-read', (_p, _q, body) => {
    const nid = body?.notificationId || body?.id
    dynamicAlerts = dynamicAlerts.map((a) =>
      a.id === nid || a.notificationId === nid || String(a.id) === String(nid) ? { ...a, unread: false } : a
    )
    return { ok: true, success: true }
  }],
  ['post', '/notifications/mark-all-read', () => {
    dynamicAlerts = dynamicAlerts.map((a) => ({ ...a, unread: false }))
    return { ok: true, success: true }
  }],
  ['post', '/api/v1/notifications/mark-all-read', () => {
    dynamicAlerts = dynamicAlerts.map((a) => ({ ...a, unread: false }))
    return { ok: true, success: true }
  }],
  ['post', '/api/v1/automation/trigger', () => {
    evaluateCertificateExpirations()
    return { status: 'triggered', message: 'Automation engine evaluated all rules', alerts: dynamicAlerts }
  }],
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
    const found = dynamicPermits.find((x) => x.id === p.id)
    if (!found) throw fail(404, `لا يوجد تصريح بالرقم ${p.id}`)
    return found
  }],
  ['get', '/permits', (_p, q) => {
    let rows = dynamicPermits.map((r) => (approvedPermits.has(r.id) ? { ...r, rawStatus: 'ACTIVE', status: 'نشط', statusTone: 'safe' } : r))
    if (q && q.type && q.type !== 'all') rows = rows.filter((r) => r.type === q.type)
    return rows
  }],
  ['post', '/permits', (_p, _q, body) => {
    const newId = 'PTW-' + String(dynamicPermits.length + 1).padStart(3, '0')
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
    dynamicPermits = [item, ...dynamicPermits]
    return item
  }],
  ['put', '/permits/:id', (p, _q, body) => {
    let target = dynamicPermits.find((x) => x.id === p.id)
    if (!target) {
      target = { id: p.id, ...body }
      dynamicPermits.unshift(target)
    } else {
      Object.assign(target, body)
    }
    return target
  }],
  ['delete', '/permits/:id', (p) => {
    dynamicPermits = dynamicPermits.filter((x) => x.id !== p.id)
    return { success: true, id: p.id }
  }],
  ['post', '/permits/:id/suspend', (p) => {
    dynamicPermits = dynamicPermits.map((x) => (x.id === p.id ? { ...x, rawStatus: 'SUSPENDED', status: 'موقوف', statusTone: 'cr' } : x))
    return { success: true, id: p.id, status: 'SUSPENDED' }
  }],
  ['post', '/permits/:id/close', (p) => {
    dynamicPermits = dynamicPermits.map((x) => (x.id === p.id ? { ...x, rawStatus: 'CLOSED', status: 'مغلق', statusTone: 'wn' } : x))
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
  ['post', '/risk/hazards', (_p, _q, body) => {
    const code = 'RSK-' + String(db.hazards.length + 1).padStart(3, '0')
    const prob = Number(body.probability) || 1
    const sev = Number(body.severity) || 1
    const score = prob * sev
    const item = {
      code,
      hazard: body.hazard || '',
      activity: body.activity || '',
      zone: body.zone || 'ورشة الصيانة',
      probability: prob,
      severity: sev,
      score,
      level: score >= 20 ? 'حرج' : score >= 15 ? 'عالي' : score >= 10 ? 'متوسط' : score >= 5 ? 'منخفض' : 'مقبول',
      residual: Number(body.residual) || 2,
      controls: body.controls || '',
      owner: body.owner || 'م. أحمد عثمان',
      reviewed: new Date().toISOString().split('T')[0],
      nextReview: new Date(Date.now() + 90 * 86400000).toISOString().split('T')[0],
      status: 'تحت التحكم'
    }
    db.hazards.unshift(item)
    return { success: true, code, message: 'تم الحفظ بنجاح' }
  }],
  ['get', '/jsa/stats', () => db.jsaStats],
  ['get', '/jsa/:id', (p) => db.jsaDetail[p.id] || null],
  ['get', '/jsa', () => db.jsaList],

  /* operations */
  ['get', '/departments', () => db.departments],
  ['get', '/inspections/schedule', () => dynamicInspectionSchedule],
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
    dynamicInspectionSchedule = [item, ...dynamicInspectionSchedule]
    return item
  }],
  ['get', '/inspections/findings', () => dynamicInspectionFindings],
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
    dynamicInspectionSchedule = [item, ...dynamicInspectionSchedule]
    if (body.findings && body.findings.length > 0) {
      dynamicInspectionFindings = [...body.findings, ...dynamicInspectionFindings]
    }
    return { success: true, item }
  }],
  ['post', '/inspections/findings/:id/status', (p, _q, body) => {
    const fid = parseInt(p.id, 10)
    const state = body.state || body.status || 'مغلق'
    dynamicInspectionFindings = dynamicInspectionFindings.map((f) =>
      f.id === fid ? { ...f, state } : f
    )
    return { success: true, id: fid, state }
  }],
  ['get', '/training/programs', () => db.trainingPrograms],
  ['get', '/training/expiring', () => {
    evaluateCertificateExpirations()
    const now = new Date()
    return dynamicTrainingExpiring.map((e) => {
      const expDate = e.expires || e.expiryDate || '2099-12-31'
      const expTime = e.expiryTime || (e.evidenceRef && e.evidenceRef.includes('@') ? e.evidenceRef.split('@')[1] : '23:59')
      const targetDt = new Date(`${expDate}T${expTime.length === 5 ? expTime + ':00' : expTime}`)
      const isExp = e.status === 'منتهية' || (!isNaN(targetDt.getTime()) && targetDt <= now)
      return {
        ...e,
        expiryTime: expTime,
        status: isExp ? 'منتهية' : 'تنتهي قريباً',
        tone: isExp ? 'cr' : 'wn',
      }
    })
  }],
  ['get', '/training/stats', () => db.trainingStats],
  ['get', '/training/schedule', () => {
    evaluateCertificateExpirations()
    return [...dynamicTrainingSchedule]
  }],
  ['post', '/training/register', (_p, _q, body) => {
    const newId = 'TRN-' + String(dynamicTrainingSchedule.length + 1).padStart(3, '0')
    const expDate = body.expiryDate || new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10)
    const expTime = body.expiryTime || '23:59'
    const targetDt = new Date(`${expDate}T${expTime.length === 5 ? expTime + ':00' : expTime}`)
    const isExpired = !isNaN(targetDt.getTime()) && targetDt <= new Date()

    const item = {
      id: newId,
      certId: dynamicTrainingSchedule.length + 1,
      employee: body.employeeName || 'محمود عبد الله',
      dept: body.dept || 'قطاع الإنتاج والتصنيع',
      course: body.courseName || 'السلامة العامة',
      provider: body.provider || 'ESCA HSE Academy',
      issueDate: body.issueDate || new Date().toISOString().slice(0, 10),
      expiryDate: expDate,
      expiryTime: expTime,
      fullExpiry: `${expDate} ${expTime}`,
      evidenceRef: body.evidenceRef || ('CERT-' + Math.floor(Math.random() * 9000 + 1000) + '@' + expTime),
      status: isExpired ? 'منتهية الصلاحية (EXPIRED)' : 'سارية ومعتمدة',
      statusTone: isExpired ? 'cr' : 'ok',
      liveNotificationTriggered: isExpired,
    }
    dynamicTrainingSchedule = [item, ...dynamicTrainingSchedule]

    const expItem = {
      id: dynamicTrainingExpiring.length + 1,
      employee: body.employeeName || 'محمود عبد الله',
      employeeNo: 'EMP-' + String(body.employeeId || 1).padStart(3, '0'),
      dept: body.dept || 'قطاع الإنتاج والتصنيع',
      certificate: body.courseName || 'السلامة العامة',
      expires: expDate,
      expiryTime: expTime,
      status: isExpired ? 'منتهية' : 'تنتهي قريباً',
      tone: isExpired ? 'cr' : 'wn',
    }
    dynamicTrainingExpiring = [expItem, ...dynamicTrainingExpiring]

    const alertItem = {
      id: 'NTF-' + Date.now(),
      notificationId: Date.now(),
      title: isExpired ? `تنبيه أتمتة السلامة: انتهاء صلاحية شهادة ${item.employee}` : `توثيق واعتماد شهادة تدريبية: ${item.employee}`,
      body: isExpired
        ? `انتهت صلاحية شهادة تدريب الموظف ${item.employee} لدورة (${item.course}) في ${item.fullExpiry} — تم تفعيل تنبيه السلامة الآلي (AUT-002).`
        : `تم توثيق واعتماد شهادة تدريب (${item.course}) للموظف ${item.employee} بنجاح في مصفوفة الكفاءة وتحديث سجلات السلامة.`,
      time: 'الآن (مباشر)',
      color: isExpired ? 'var(--crit)' : 'var(--safe)',
      type: isExpired ? 'AUTOMATION_CERTIFICATE_EXPIRY' : 'TRAINING',
      to: '/training',
      unread: true,
    }
    dynamicAlerts = [alertItem, ...dynamicAlerts]

    return { ...item, notification: alertItem }
  }],
  ['get', '/hazmat/chemicals', () => db.chemicals],
  ['get', '/hazmat/stats', () => db.hazmatStats],
  ['get', '/hazmat/compatibility', () => db.compatibility],
  ['get', '/occupational-health/exams', () => db.healthExams],
  ['get', '/occupational-health/stats', () => db.healthStats],
  ['get', '/occupational-health/exposure', () => db.exposureMonitoring],
  ['get', '/occupational-health/schedule', () => dynamicHealthSchedule],
  ['post', '/occupational-health/exams', (_p, _q, body) => {
    const newId = 'HEX-' + String(dynamicHealthSchedule.length + 1).padStart(3, '0')
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
    dynamicHealthSchedule = [item, ...dynamicHealthSchedule]
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

  /* JSA & Task Safety Analysis */
  ['get', '/jsa/stats', () => ({
    approved: dynamicJsaList.filter(j => j.statusId === 3 || j.rawStatus === 'APPROVED').length || 32,
    needsReview: dynamicJsaList.filter(j => j.statusId === 1 || j.statusId === 2).length || 4,
    linkedToPermits: dynamicJsaList.filter(j => j.linkedPermitId).length || 28,
    criticalTaskCoverage: 96,
    total: dynamicJsaList.length
  })],
  ['get', '/jsa/available-permits', () => (dynamicPermits || []).map(p => ({
    id: p.id || 'PTW-001',
    permitId: parseInt(String(p.id).replace(/\D+/g, '') || '1', 10),
    description: p.workDescription || p.description || 'أعمال صيانة',
    zone: p.zone || 'المنطقة الرئيسية',
    type: p.permitType || 'HOT_WORK',
    typeLabel: p.typeLabel || 'عمل ساخن',
    status: p.status || 'ACTIVE',
    linkedJsaId: p.jsaId || null
  }))],
  ['get', '/jsa', (_p, q) => {
    let result = [...dynamicJsaList]
    if (q.q) {
      const qLower = q.q.toLowerCase()
      result = result.filter(j => j.task?.toLowerCase().includes(qLower) || j.id?.toLowerCase().includes(qLower) || j.zone?.toLowerCase().includes(qLower))
    }
    return result
  }],
  ['get', '/jsa/:id', (p) => {
    const found = dynamicJsaList.find(j => j.id === p.id || String(j.numericId) === p.id) || dynamicJsaList[0]
    if (!found) return null
    const steps = dynamicJsaSteps[found.id] || dynamicJsaSteps['JSA-001'] || []
    return {
      ...found,
      steps,
      linkedPermits: found.linkedPermitId ? [{
        permitId: found.linkedPermitId,
        permitCode: `PTW-${String(found.linkedPermitId).padStart(3, '0')}`,
        workDescription: found.task,
        type: found.permitType
      }] : []
    }
  }],
  ['post', '/jsa', (_p, _q, body) => {
    const nextId = 'JSA-' + String(dynamicJsaList.length + 1).padStart(3, '0')
    const numId = dynamicJsaList.length + 1
    const newItem = {
      id: nextId,
      numericId: numId,
      jsaId: numId,
      task: body.taskName || body.task || 'تحليل سلامة مهمة جديدة',
      taskName: body.taskName || body.task || 'تحليل سلامة مهمة جديدة',
      zone: body.zone || 'خطوط العزل CCV',
      zoneId: 1,
      steps: (body.steps || []).length || 1,
      criticalSteps: 1,
      permitType: body.permitType || 'HOT_WORK',
      linkedPermit: body.linkPermitId ? `عمل ساخن (${body.linkPermitId})` : 'عمل ساخن',
      linkedPermitId: body.linkPermitId ? parseInt(String(body.linkPermitId).replace(/\D+/g, ''), 10) : null,
      permitRequired: body.permitRequired !== false,
      reviewed: new Date().toISOString().slice(0, 10),
      status: 'معتمد',
      rawStatus: 'APPROVED',
      statusId: 3,
      tone: 'ok',
      inherentScore: body.inherentScore || 16,
      residualScore: body.residualScore || 4
    }
    dynamicJsaList = [newItem, ...dynamicJsaList]
    if (body.steps && Array.isArray(body.steps)) {
      dynamicJsaSteps[nextId] = body.steps.map((st, i) => ({
        id: Date.now() + i,
        stepId: Date.now() + i,
        stepNo: i + 1,
        step: st.step,
        hazard: st.hazard,
        control: st.control,
        before: st.before || 16,
        after: st.after || 4,
        responsible: st.responsible || 'مشرف الوردية'
      }))
    }
    return newItem
  }],
  ['patch', '/jsa/:id/approve', (p) => {
    dynamicJsaList = dynamicJsaList.map(j => (j.id === p.id || String(j.numericId) === p.id) ? { ...j, status: 'معتمد', rawStatus: 'APPROVED', statusId: 3, tone: 'ok' } : j)
    return { success: true, message: 'Approved' }
  }],
  ['delete', '/jsa/:id', (p) => {
    dynamicJsaList = dynamicJsaList.filter(j => j.id !== p.id && String(j.numericId) !== p.id)
    return { success: true, message: 'Deleted' }
  }],
  ['post', '/jsa/:id/steps', (p, _q, body) => {
    const list = dynamicJsaSteps[p.id] || []
    const newStep = {
      id: Date.now(),
      stepId: Date.now(),
      stepNo: list.length + 1,
      step: body.step,
      hazard: body.hazard,
      control: body.control,
      before: body.before || 15,
      after: body.after || 4,
      responsible: body.responsible || 'مشرف الوردية'
    }
    dynamicJsaSteps[p.id] = [...list, newStep]
    return { success: true, step: newStep }
  }],
  ['delete', '/jsa/:id/steps/:stepId', (p) => {
    const list = dynamicJsaSteps[p.id] || []
    dynamicJsaSteps[p.id] = list.filter(s => String(s.id) !== p.stepId && String(s.stepId) !== p.stepId)
    return { success: true, message: 'Step deleted' }
  }],
  ['post', '/jsa/:id/link-permit', (p, _q, body) => {
    const pCode = body.permitId || 'PTW-001'
    dynamicJsaList = dynamicJsaList.map(j => (j.id === p.id || String(j.numericId) === p.id) ? {
      ...j,
      linkedPermit: `${j.permitType} (${pCode})`,
      linkedPermitId: parseInt(String(pCode).replace(/\D+/g, '') || '1', 10)
    } : j)
    return { success: true, message: `تم ربط تصريح العمل (${pCode}) بتحليل السلامة (${p.id}) بنجاح.` }
  }],

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

  /* hazmat & chemicals */
  ['get', '/hazmat/stats', () => ({
    total: dynamicChemicals.length,
    active: dynamicChemicals.filter(c => c.statusId === 1 || c.status === 'ACTIVE').length,
    flammable: dynamicChemicals.filter(c => String(c.ghsClasses || c.ghs || '').toUpperCase().includes('FLAMMABLE')).length,
    corrosive: dynamicChemicals.filter(c => String(c.ghsClasses || c.ghs || '').toUpperCase().includes('CORROSIVE')).length,
    toxic: dynamicChemicals.filter(c => String(c.ghsClasses || c.ghs || '').toUpperCase().includes('TOXIC')).length,
    sdsExpired: dynamicSdsList.filter(s => s.isExpired).length,
    sdsDueSoon: dynamicSdsList.filter(s => s.isDueSoon).length,
    spillKits: 14,
    storageAudits: 6,
    complianceRate: 98.2,
    success: true
  })],
  ['get', '/hazmat/chemicals', (_p, q) => {
    let list = [...dynamicChemicals]
    if (q.query || q.q) {
      const s = (q.query || q.q).toLowerCase()
      list = list.filter(c => (c.name || '').toLowerCase().includes(s) || (c.tradeName || '').toLowerCase().includes(s) || (c.cas || '').includes(s))
    }
    if (q.ghs && q.ghs !== 'ALL') {
      list = list.filter(c => (c.ghsClasses || '').toUpperCase().includes(q.ghs.toUpperCase()))
    }
    if (q.status && q.status !== 'ALL') {
      list = list.filter(c => c.status === q.status || String(c.statusId) === q.status)
    }
    return list
  }],
  ['get', '/hazmat/chemicals/:id', (p) => {
    const found = dynamicChemicals.find(c => String(c.id) === p.id || c.code === p.id)
    return found || dynamicChemicals[0]
  }],
  ['post', '/hazmat/chemicals', (_p, _q, body) => {
    const newId = dynamicChemicals.length + 1
    const item = {
      id: newId,
      chemicalId: newId,
      code: `CHM-${String(newId).padStart(3, '0')}`,
      name: body.tradeName || body.name || 'مادة كيميائية جديدة',
      tradeName: body.tradeName || body.name || 'مادة كيميائية جديدة',
      chemicalName: body.chemicalName || body.tradeName || 'Chemical',
      cas: body.casNumber || 'N/A',
      casNumber: body.casNumber || 'N/A',
      supplier: body.supplier || 'Elsewedy Supply',
      quantity: Number(body.quantity || 100),
      unit: body.unit || 'L',
      qty: `${body.quantity || 100} ${body.unit || 'L'}`,
      ghsClasses: body.ghsClasses || 'FLAMMABLE',
      ghs: body.ghsClasses || 'GHS02 سريع الاشتعال',
      tone: 'crit',
      class: body.storageClass || 'Class 3',
      storageClass: body.storageClass || 'Class 3',
      zoneId: body.zoneId || 9,
      location: 'مخزن المواد الكيميائية الرئيسي',
      status: 'ACTIVE',
      statusId: 1,
      statusAr: 'نشط ومصرح به',
      sds: '2027-01',
      sdsVersion: body.sdsVersion || 'Rev 1',
      emergencySummary: body.emergencySummary || 'عزل المصدر واستخدام مهمات الوقاية الملائمة.'
    }
    dynamicChemicals.unshift(item)
    return item
  }],
  ['put', '/hazmat/chemicals/:id', (p, _q, body) => {
    dynamicChemicals = dynamicChemicals.map(c => (String(c.id) === p.id || c.code === p.id) ? { ...c, ...body } : c)
    return { success: true, message: 'تم تحديث بيانات المادة الكيميائية بنجاح' }
  }],
  ['delete', '/hazmat/chemicals/:id', (p) => {
    dynamicChemicals = dynamicChemicals.filter(c => String(c.id) !== p.id && c.code !== p.id)
    return { success: true, message: 'تم حذف المادة الكيميائية بنجاح' }
  }],
  ['get', '/hazmat/compatibility', () => ({
    groups: ["قابل للاشتعال (Flammable)", "أكّال حمضي (Acidic)", "أكّال قاعدي (Basic)", "مؤكسد (Oxidizer)", "غازات مضغوطة (Gases)"],
    grid: [
      ["✓", "!", "!", "X", "!"],
      ["!", "✓", "X", "X", "!"],
      ["!", "X", "✓", "!", "!"],
      ["X", "X", "!", "✓", "X"],
      ["!", "!", "!", "X", "✓"]
    ]
  })],
  ['get', '/hazmat/sds', (_p, q) => {
    let list = [...dynamicSdsList]
    if (q.query || q.q) {
      const s = (q.query || q.q).toLowerCase()
      list = list.filter(item => (item.tradeName || '').toLowerCase().includes(s) || (item.chemicalName || '').toLowerCase().includes(s) || (item.fileRef || '').toLowerCase().includes(s))
    }
    if (q.status && q.status !== 'ALL') {
      list = list.filter(item => item.status === q.status)
    }
    return list
  }],
  ['post', '/hazmat/sds', (_p, _q, body) => {
    const sId = dynamicSdsList.length + 1
    const newSds = {
      sdsId: sId,
      id: sId,
      chemicalId: body.chemicalId || 1,
      chemicalCode: `CHM-${String(body.chemicalId || 1).padStart(3, '0')}`,
      tradeName: 'DURACLEAN 200',
      versionNo: body.versionNo || 'Rev 2',
      issueDate: body.issueDate || '2026-01-10',
      expiryDate: body.expiryDate || '2028-01-10',
      language: body.language || 'EN/AR',
      fileRef: `SDS-ESCA-00${sId}.pdf`,
      emergencySummary: body.emergencySummary || 'عزل المصدر واستخدام مهمات الوقاية.',
      status: 'CURRENT',
      statusAr: 'سارية ومحدثة',
      daysToExpiry: 365,
      isExpired: false,
      isDueSoon: false,
      tone: 'safe'
    }
    dynamicSdsList.unshift(newSds)
    return { success: true, sdsId: sId, message: 'تم حفظ صحيفة SDS بنجاح.' }
  }],
  ['delete', '/hazmat/sds/:id', (p) => {
    dynamicSdsList = dynamicSdsList.filter(s => String(s.sdsId) !== p.id && String(s.id) !== p.id)
    return { success: true, message: 'تم حذف صحيفة SDS بنجاح.' }
  }],
  ['post', '/ask', (_p, _q, body) => {
    const q = body?.question || ''
    const res = answer(q)
    return {
      session_id: 'mock-session-' + Date.now(),
      answer: res.answer,
      tool_calls: (res.tools || []).map(t => ({
        tool_name: t.name,
        query_summary: `${t.name} (${t.rowCount || 0} records)`,
        rows_returned: t.rowCount || 0,
      })),
      tools: res.tools || [],
      model_used: 'ESCA Intelligent Assistant (Mock Engine)',
    }
  }],
  ['post', '/api/ask', (_p, _q, body) => {
    const q = body?.question || ''
    const res = answer(q)
    return {
      session_id: 'mock-session-' + Date.now(),
      answer: res.answer,
      tool_calls: (res.tools || []).map(t => ({
        tool_name: t.name,
        query_summary: `${t.name} (${t.rowCount || 0} records)`,
        rows_returned: t.rowCount || 0,
      })),
      tools: res.tools || [],
      model_used: 'ESCA Intelligent Assistant (Mock Engine)',
    }
  }],
  ['get', '/suggestions', () => [
    "ما هي الحوادث المفتوحة حالياً وما درجة خطورتها؟",
    "اعرض تصاريح العمل النشطة والمنتهية في الموقع ePTW",
    "افحص تعارضات العمليات المتزامنة SIMOPS في منطقة الإنتاج",
    "ما هي إحصائيات ونسبة الامتثال لجولات التفتيش والسلامة؟",
    "جدول فحص سلامة روتيني لمنطقة خطوط العزل CCV الأسبوع القادم",
    "ما هي مطافئ الحريق التي تحتاج فحص دوري أو إعادة تعبئة؟",
    "صرف مهمة وقاية شخصية (PPE) للموظف وتحديث المخزون",
    "اعرض أحدث تنبيهات حساسات الغازات والحرارة الذكية IoT",
    "احسب مؤشرات TRIR و LTIFR لشهر يوليو 2026",
    "ما هي القواعد الذهبية للسلامة (ESCA Golden Rules)؟",
  ]],
  ['get', '/api/v1/notifications', () => dynamicAlerts],
  ['post', '/api/v1/notifications/mark-read', (_p, _q, body) => {
    const n = dynamicAlerts.find(a => a.id === body?.notificationId || a.id === body?.id)
    if (n) n.unread = false
    return { success: true }
  }],
  ['post', '/api/v1/notifications/mark-all-read', () => {
    dynamicAlerts.forEach(a => a.unread = false)
    return { success: true }
  }],
  ['get', '/api/v1/hazmat/chemicals', (_p, q) => {
    let list = [...dynamicChemicals]
    if (q.query || q.q) {
      const s = (q.query || q.q).toLowerCase()
      list = list.filter(c => (c.name || '').toLowerCase().includes(s) || (c.tradeName || '').toLowerCase().includes(s) || (c.cas || '').includes(s))
    }
    if (q.ghs && q.ghs !== 'ALL') {
      list = list.filter(c => (c.ghsClasses || '').toUpperCase().includes(q.ghs.toUpperCase()))
    }
    if (q.status && q.status !== 'ALL') {
      list = list.filter(c => c.status === q.status || String(c.statusId) === q.status)
    }
    return list
  }],
  ['get', '/api/v1/hazmat/stats', () => db.hazmatStats || ({ totalChemicals: dynamicChemicals.length, activeChemicals: dynamicChemicals.length, flammableCount: 12, corrosiveCount: 6, toxicCount: 5, totalVolumeLiters: 1540.0, sdsCurrentCount: dynamicChemicals.length, sdsExpiredCount: 0, complianceRate: 100 })],
  ['get', '/health', () => ({ status: 'ok', service: 'esca-agent' })],
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
