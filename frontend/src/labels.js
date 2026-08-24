/**
 * Arabic labels for the coded values that come out of the company sheets.
 *
 * The sheets store controlled vocabularies in English SCREAMING_CASE
 * (`HOT_WORK`, `INVESTIGATING`, `DUE_SOON`). Those codes are the contract with
 * the backend and must travel unchanged — so translation happens here, at the
 * edge, and only for display.
 *
 * Free text from the sheets (incident titles, hazard descriptions, control
 * measures) is shown exactly as provided. Translating it would mean inventing
 * content that is not in the source data.
 *
 * `t(code)` falls back to the raw code, so an unmapped value from a future
 * sheet drop shows up visibly rather than rendering as blank.
 */

const AR = {
  /* --- severity / priority / risk --- */
  CRITICAL: 'حرجة',
  HIGH: 'عالية',
  MAJOR: 'كبيرة',
  MEDIUM: 'متوسطة',
  MODERATE: 'متوسطة',
  MINOR: 'بسيطة',
  LOW: 'منخفضة',
  INFO: 'للعلم',
  NORMAL: 'طبيعي',
  WARNING: 'تحذير',

  /* --- incident types --- */
  FIRST_AID: 'إسعاف أولي',
  LTI: 'إصابة مُعطِّلة',
  NEAR_MISS: 'شبه حادث',
  PROPERTY_DAMAGE: 'ضرر بالممتلكات',
  UNSAFE_ACT: 'سلوك غير آمن',
  UNSAFE_CONDITION: 'وضع غير آمن',

  /* --- permit types --- */
  HOT_WORK: 'عمل ساخن',
  ELECTRICAL: 'عمل كهربائي',
  WORK_AT_HEIGHT: 'عمل بالمرتفعات',
  CONFINED_SPACE: 'أماكن مغلقة',
  MECHANICAL_LOTO: 'ميكانيكي / LOTO',
  EXCAVATION: 'حفر وأعمال مدنية',

  /* --- statuses --- */
  ACTIVE: 'نشط',
  OPEN: 'مفتوح',
  CLOSED: 'مغلق',
  INVESTIGATING: 'تحت التحقيق',
  CAPA_ASSIGNED: 'إجراء تصحيحي',
  PENDING: 'بانتظار',
  PENDING_APPROVAL: 'بانتظار الموافقة',
  PENDING_VERIFICATION: 'بانتظار التحقق',
  IN_PROGRESS: 'جارٍ التنفيذ',
  COMPLETED: 'مكتمل',
  APPROVED: 'معتمد',
  REJECTED: 'مرفوض',
  SUSPENDED: 'موقوف',
  BLOCKED: 'محجوب',
  CANCELLED: 'مُلغى',
  DRAFT: 'مسودة',
  SCHEDULED: 'مجدول',
  PLANNED: 'مخطط',
  OVERDUE: 'متأخر',
  DUE_SOON: 'ينتهي قريباً',
  EXPIRED: 'منتهي',
  VALID: 'صالح',
  CURRENT: 'ساري',
  MITIGATED: 'تم تخفيضه',
  RESOLVED: 'تم حله',
  REFERRED: 'محوّل',
  PARTIAL: 'جزئي',
  PARTIAL_FAILURE: 'فشل جزئي',
  FAILED: 'فشل',
  SUCCESS: 'ناجح',
  DENIED: 'مرفوض',
  MISSING_CURRENT_VERSION: 'نسخة غير محدّثة',
  RENEWAL_BOOKED: 'التجديد محجوز',
  FALSE_POSITIVE: 'إنذار كاذب',
  ACTION_REQUIRED: 'يحتاج إجراء',
  OPERATIONAL: 'يعمل',
  MAINTENANCE: 'تحت الصيانة',
  OFFLINE: 'غير متصل',
  ONLINE: 'متصل',
  CONNECTED: 'متصل',
  DEPLOYED: 'مُشغَّل',
  TRAINING: 'تحت التدريب',
  TESTING: 'تحت الاختبار',
  TEST: 'اختبار',
  MODEL_REVIEW: 'مراجعة النموذج',
  PHASED_OUT: 'خارج الخدمة',
  QUARANTINED: 'معزول',
  CHARGING: 'قيد الشحن',
  UNREAD: 'غير مقروء',
  READ: 'مقروء',

  /* --- automation / review flags --- */
  OK: 'سليم',
  NO_ACTION: 'لا إجراء',
  EXPIRES_TODAY: 'ينتهي اليوم',
  DUE_7_DAYS: 'خلال 7 أيام',
  DUE_14_DAYS: 'خلال 14 يوم',
  DUE_30_DAYS: 'خلال 30 يوم',
  REVIEW_REQUIRED: 'يحتاج مراجعة',
  REVIEW_OVERDUE: 'المراجعة متأخرة',
  BELOW_THRESHOLD: 'تحت حد الطلب',

  /* --- departments & zones --- */
  PRODUCTION: 'إنتاج',
  OPERATIONS: 'تشغيل',
  TECHNICAL: 'فني',
  ADMIN: 'إداري',
  CONTROL: 'رقابة',
  HEALTH: 'صحة مهنية',
  PRODUCTION_LINE: 'خط إنتاج',
  PACKING: 'تعبئة',
  WORKSHOP: 'ورشة',
  WAREHOUSE: 'مخزن',
  LOGISTICS: 'خدمات لوجستية',
  LAB: 'معمل',
  OFFICE: 'مكاتب',
  CLINIC: 'عيادة',
  CHEMICAL_STORAGE: 'تخزين كيماويات',

  /* --- inspections & findings --- */
  SAFETY_WALK: 'جولة سلامة',
  FIRE_READINESS: 'جاهزية الحريق',
  PPE_COMPLIANCE: 'الالتزام بمعدات الوقاية',
  HOUSEKEEPING: 'الترتيب والنظافة',
  FORKLIFT: 'الرافعات الشوكية',
  MACHINE_GUARDING: 'حواجز الماكينات',
  FALL_PROTECTION: 'الحماية من السقوط',
  LOTO: 'العزل والتأمين',
  PPE: 'معدات الوقاية',
  SDS: 'صحائف بيانات السلامة',
  WASTE: 'المخلفات',
  FIRE_EQUIPMENT: 'معدات الحريق',

  /* --- controls hierarchy --- */
  ELIMINATION: 'إزالة الخطر',
  SUBSTITUTION: 'استبدال',
  ENGINEERING: 'ضوابط هندسية',
  ADMINISTRATIVE: 'ضوابط إدارية',

  /* --- PPE categories --- */
  HEAD: 'الرأس',
  EYES: 'العين',
  FACE: 'الوجه',
  HANDS: 'اليد',
  FEET: 'القدم',
  BODY: 'الجسم',
  HEARING: 'السمع',
  RESPIRATORY: 'الجهاز التنفسي',

  /* --- sensors & AI --- */
  VOC: 'مركّبات عضوية طيّارة',
  NOISE: 'ضوضاء',
  OXYGEN: 'أكسجين',
  TEMPERATURE: 'حرارة',
  WBGT: 'إجهاد حراري',
  PM2_5: 'جسيمات PM2.5',
  ACETYLENE_LEL: 'أسيتيلين',
  LPG_LEL: 'غاز مسال',
  PPE_VIOLATION: 'مخالفة معدات وقاية',
  RESTRICTED_ZONE: 'دخول منطقة محظورة',
  MAN_DOWN: 'سقوط عامل',
  SMOKE_DETECTION: 'كشف دخان',
  FIRE_DETECTION: 'كشف حريق',
  SPILL_DETECTION: 'كشف انسكاب',
  FORKLIFT_PROXIMITY: 'اقتراب رافعة شوكية',
  OBJECT_DETECTION: 'كشف الأجسام',
  POSE_DETECTION: 'كشف الوضعية',
  EVENT_DETECTION: 'كشف الأحداث',
  ZONE_INTRUSION: 'اختراق منطقة',
  SEGMENTATION: 'تقسيم الصورة',
  PROXIMITY_EVENT: 'حدث اقتراب',

  /* --- exposures & health --- */
  HEAT: 'إجهاد حراري',
  CHEMICALS: 'مواد كيميائية',
  VISION: 'النظر',
  RESPIRATOR: 'كمامات',
  GENERAL: 'عام',
  FIT: 'لائق',
  FIT_WITH_RESTRICTIONS: 'لائق بقيود',
  CONTROLLED_WITH_PPE: 'مضبوط بمعدات وقاية',
  VENTILATION_AND_RESPIRATOR: 'تهوية وكمامة',
  FUME_HOOD_AND_GLOVES: 'شفاط وقفازات',
  PTW_AND_GAS_TEST: 'تصريح وقياس غازات',
  PTW_AND_FALL_PROTECTION: 'تصريح وحماية من السقوط',
  WORK_REST_HYDRATION: 'دورات راحة وترطيب',
  FIT_TEST_REQUIRED: 'يحتاج اختبار إحكام',
  LICENSE_AND_REVIEW: 'رخصة ومراجعة',
  ACCESS_CONTROL: 'تحكم في الدخول',
  CONFIDENTIAL: 'سري',
  RESTRICTED: 'مقيّد',

  /* --- frequency --- */
  DAILY: 'يومي',
  WEEKLY: 'أسبوعي',
  MONTHLY: 'شهري',
  QUARTERLY: 'ربع سنوي',
  ANNUAL: 'سنوي',
  HOURLY: 'كل ساعة',
  REAL_TIME: 'لحظي',
  STREAMING: 'بث مستمر',
  AS_NEEDED: 'عند الحاجة',

  /* --- misc --- */
  INTERNAL: 'داخلي',
  CONTRACTOR: 'مقاول',
  YES: 'نعم',
  NO: 'لا',
  NOT_CHECKED: 'لم يُفحص',
  CORRECTIVE: 'تصحيحي',
  PREVENTIVE: 'وقائي',
  VERIFIED: 'تم التحقق',
  NOT_REQUIRED: 'غير مطلوب',
  USER: 'مستخدم',
  SERVICE: 'خدمة',
  UNKNOWN: 'غير معروف',
  BIDIRECTIONAL: 'ثنائي الاتجاه',
  INBOUND: 'وارد',
  ERP: 'نظام موارد المؤسسة',
  HUMAN_RESOURCES: 'الموارد البشرية',
  INDUSTRIAL_IOT: 'إنترنت الأشياء الصناعي',
  PHYSICAL_ACCESS: 'التحكم في الدخول',
  VIDEO_MANAGEMENT: 'إدارة الكاميرات',
  ALL_EMPLOYEES: 'كل الموظفين',
}

/** Roles carry a description in the sheet; the Arabic label is ours. */
export const ROLE_AR = {
  HSE_MANAGER: 'مدير السلامة والصحة المهنية',
  HSE_OFFICER: 'أخصائي سلامة',
  OCCUPATIONAL_DOCTOR: 'طبيب الصحة المهنية',
  DEPARTMENT_MANAGER: 'مدير قسم',
  SHIFT_SUPERVISOR: 'مشرف وردية',
  MAINTENANCE_TECHNICIAN: 'فني صيانة',
  WORKER: 'عامل',
  CONTRACTOR: 'مقاول',
  AUDITOR: 'مدقّق',
  AUTOMATION_SERVICE: 'خدمة الأتمتة',
}

/** Translate a coded value. Unknown codes come back unchanged, on purpose. */
export function t(code) {
  if (code == null || code === '') return '—'
  return AR[code] ?? String(code)
}

/** Translate a semicolon-joined list, e.g. "FLAMMABLE;IRRITANT". */
export function tList(value, sep = ' · ') {
  if (!value) return '—'
  return String(value)
    .split(';')
    .map((v) => t(v.trim()))
    .join(sep)
}

/** Map a coded value onto the console's pill tones. */
export function tone(code) {
  const CR = ['CRITICAL', 'EXPIRED', 'OVERDUE', 'BLOCKED', 'REJECTED', 'SUSPENDED', 'FAILED', 'DENIED', 'HIGH', 'MAJOR', 'BELOW_THRESHOLD', 'REVIEW_OVERDUE', 'MISSING_CURRENT_VERSION', 'ACTION_REQUIRED']
  const WN = ['DUE_SOON', 'MEDIUM', 'MODERATE', 'WARNING', 'PENDING', 'PENDING_APPROVAL', 'PENDING_VERIFICATION', 'IN_PROGRESS', 'INVESTIGATING', 'PARTIAL', 'PARTIAL_FAILURE', 'REVIEW_REQUIRED', 'EXPIRES_TODAY', 'DUE_7_DAYS', 'DUE_14_DAYS', 'MAINTENANCE', 'OPEN']
  const OK = ['VALID', 'ACTIVE', 'CLOSED', 'COMPLETED', 'APPROVED', 'OK', 'SUCCESS', 'CURRENT', 'FIT', 'OPERATIONAL', 'CONNECTED', 'DEPLOYED', 'RESOLVED', 'MITIGATED', 'NORMAL', 'ONLINE', 'VERIFIED', 'YES']
  if (CR.includes(code)) return 'cr'
  if (WN.includes(code)) return 'wn'
  if (OK.includes(code)) return 'ok'
  return 'nu'
}

export default t
