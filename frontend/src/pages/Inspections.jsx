import { useState, useMemo, useEffect } from 'react'
import {
  Async,
  Btn,
  Card,
  CardBody,
  CardHead,
  Field,
  Grid,
  Kpi,
  KpiRow,
  PageHeader,
  Pill,
  StatLine,
  Table,
  Tag,
  Timeline,
  TimelineItem,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import Modal from '../components/Modal.jsx'
import { inspections as inspApi, fire as fireApi } from '../api/endpoints.js'
import { getLocalDateString, useApi, useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

const FIELD_TYPES = [
  { name: 'نعم / لا / لا ينطبق', desc: 'خيارات التقييم الثنائية السريعة (Pass / Fail / NA) مع درجات الامتثال' },
  { name: 'اختيار متعدد', desc: 'قائمة خيارات محددة مسبقاً لاختيار بند واحد أو عدة بنود' },
  { name: 'قيمة رقمية بحدود', desc: 'إدخال قياسات (حرارة، ضغط، مسافة) مع التحقق من الحدود المسموحة' },
  { name: 'صورة إلزامية', desc: 'إلزام المفتش بالتقاط صورة من كاميرا الهاتف كدليل إثبات للمخالفة' },
  { name: 'نص حر', desc: 'حقل لوصف المشاهدات وتدوين الملاحظات التفصيلية' },
  { name: 'تاريخ', desc: 'محدد تاريخ لتواريخ المعايرة والصيانة وانتهاء الصلاحية' },
  { name: 'اختيار موظف', desc: 'تحديد المسؤول المباشر عن تصحيح الملاحظة من سجل العاملين' },
  { name: 'تقييم 1-5', desc: 'مقياس ليكرت لتقييم مستوى النظافة أو السلوك المهني' },
  { name: 'قراءة حساس', desc: 'ربط مباشر لقراءة مستشعرات IoT وغازات البيئة المحيطة' },
  { name: 'توقيع', desc: 'توقيع إلكتروني للمفتش ورئيس الوردية لاعتماد المحضر' },
]

const ZONES = [
  'خطوط العزل CCV',
  'عنبر السحب والجدل',
  'محطة المعالجة والتغليف',
  'مختبر الجودة والاختبارات',
  'محطة المحولات الرئيسية 11kV',
  'ورشة الصيانة الميكانيكية',
  'محطة التبريد المركزي ومعالجة المياه',
  'مبنى الخدمات والعيادة والمكاتب',
  'المستودع الرئيسي للمواد الخام',
  'رصيف الشحن والتفريغ الخارجي',
]

const INSPECTORS = [
  'م. مصطفى (مدير السلامة)',
  'م. كريم حسني (مسؤول سلامة ميداني)',
  'م. سامح فوزي (مسؤول سلامة)',
  'م. طارق كمال (مهندس صيانة)',
  'م. أحمد عثمان (مشرف إنتاج)',
]

const TEMPLATE_DEFINITIONS = {
  'ISO 45001 — تدقيق السلامة والصحة المهنية': {
    name: 'ISO 45001 — تدقيق داخلي للسلامة والصحة المهنية',
    authority: 'International Organization for Standardization',
    itemCount: 112,
    category: 'نظام إدارة السلامة الشامل',
    items: [
      'التزام العاملين بارتداء مهمات الوقاية الشخصية (PPE) المقررة بالمنطقة',
      'مسارات الهروب وأبواب الطوارئ خالية تماماً من أية عوائق أو مواد مخزنة',
      'سريان وتوثيق تصاريح العمل (PTW) للأعمال الساخنة والحرجة بالموقع',
      'حواجز الأمان والحساسات الضوئية على ماكينات السحب والعزل تعمل بكفاءة',
      'صناديق الإسعافات الأولية متوفرة ومكتملة المحتويات وبها سجل استخدام',
      'تأريض اللوحات الكهربائية وسلامة التوصيلات وعدم وجود أسلاك مكشوفة',
      'تهوية بيئة العمل وقياس نسب الانبعاثات الحرارية والغبار ضمن الحدود الآمنة',
      'تواجد سجل إرشادات السلامة (Toolbox Talk) اليومي موقعاً من المشرفين',
    ],
  },
  'ISO 14001 — تدقيق بيئي': {
    name: 'ISO 14001 — تدقيق بيئي وإدارة المخلفات والموارد',
    authority: 'ISO Environmental Management Standard',
    itemCount: 86,
    category: 'البيئة والاستدامة',
    items: [
      'فصل المخلفات الصناعية الصلبة والخطرة في حاويات مخصصة ومميزة بالألوان',
      'أحواض الاحتواء الثانوي (Secondary Containment) للبراميل الكيميائية سليمة',
      'خلو شبكات الصرف الصناعي من أية تسريبات زيوت أو مذيبات هيدروكربونية',
      'فلاتر شفط الأدخنة والأتربة في عنبر التصنيع تعمل بكفاءة ودون انسداد',
      'سجلات التخلص الآمن من النفايات الخطرة محدثة ومطابقة للاشتراطات البيئية',
      'ترشيد استهلاك مياه التبريد المركزي وخلو الشبكة من الهدر والتسريب',
    ],
  },
  'OSHA General Industry — السلامة العامة': {
    name: 'OSHA General Industry — معايير السلامة الصناعية الأمريكية',
    authority: 'US Occupational Safety and Health Administration (29 CFR 1910)',
    itemCount: 148,
    category: 'السلامة العامة والصناعية',
    items: [
      'خلو أسطح وممرات العمل (Walking-Working Surfaces) من مخاطر الانزلاق والتعثر',
      'مسافة خلوص لا تقل عن 36 بوصة (90 سم) أمام كافة اللوحات الكهربائية الرئيسية',
      'دشاش الطوارئ ومحطات غسيل العيون (Eye Wash) يمكن الوصول إليها خلال 10 ثوانٍ',
      'حواجز الحماية (Machine Guarding) لنقاط التشغيل والتروس الناقلة للحركة',
      'فحص شوكات الرافعات الشوكية وحزام الأمان وأجهزة الإنذار الصوتي والضوئي',
      'تطبيق إجراءات العزل والإغلاق ووضع بطاقات التحذير (Lockout/Tagout - LOTO)',
    ],
  },
  'NFPA — أنظمة ومعدات الإطفاء والإنذار': {
    name: 'NFPA — أنظمة ومعدات الإطفاء والإنذار والوقاية من الحريق',
    authority: 'National Fire Protection Association (NFPA 10, 25, 72)',
    itemCount: 64,
    category: 'الحماية من الحريق',
    items: [
      'فحص ضغط طفايات الحريق وخلو الخراطيم من الشروخ وسلامة تيلة الأمان والختم',
      'بطاقة التفتيش الشهري معلقة على كل مطفأة وموقعة من مسؤول السلامة',
      'خراطيم الحريق الرطبة معلقة وسليمة والصمامات سهلة الفتح ولا تسرب',
      'لوحة إنذار الحريق المركزية خالية من أية أعطال أو إشارات خطأ (Faults)',
      'كواشف الدخان والحرارة وأزرار الإنذار اليدوية (Break Glass) نظيفة وغير معاقة',
      'إنارة الطوارئ واللوحات الإرشادية المضيئة لمخارج الطوارئ تعمل بكفاءة عند انقطاع التيار',
    ],
  },
  'BBS — التفتيش السلوكي والممارسات': {
    name: 'BBS — التفتيش والملاحظة السلوكية (Behavior-Based Safety)',
    authority: 'DuPont Bradley HSE Maturity Framework',
    itemCount: 32,
    category: 'السلوكيات والممارسات',
    items: [
      'وضعية الجسم السليمة وتجنب الانحناء الخاطئ أثناء رفع وحمل الأوزان اليدوية',
      'الوعي بخط النار (Line of Fire) ومناطق النقاط العمياء لحركة المعدات الثقيلة',
      'استخدام الأداة المناسبة للعمل وعدم استخدام أدوات يدوية تالفة أو معدلة عشوائياً',
      'عدم استخدام الهواتف المحمولة أو التشتت أثناء تشغيل الماكينات أو القيادة',
      'التدخل الإيجابي الفوري (Peer Intervention) عند ملاحظة تصرف غير آمن من زميل',
    ],
  },
  '5S — الترتيب والنظافة الصناعية': {
    name: '5S — منهجية الترتيب والنظافة والترتيب اليابانية',
    authority: 'Lean Manufacturing & Industrial Housekeeping',
    itemCount: 25,
    category: 'الترتيب والنظافة الصناعية',
    items: [
      'التصنيف والفرز (Sort): إزالة كافة المواد والأدوات التالفة وغير اللازمة من الموقع',
      'الترتيب والتنظيم (Set in Order): وضع كل أداة في مكانها المخصص والمحدد بعلامات أرضية',
      'التنظيف والتلميع (Shine): نظافة الماكينات والأرضيات وخلوها من بقع الزيوت والغبار',
      'التقييس والمعايرة (Standardize): الالتزام بترميز الألوان والمعايير البصرية المعتمدة',
      'الاستدامة والانضباط (Sustain): إجراء التدقيق الذاتي اليومي والمحافظة المستمرة على المستوى',
    ],
  },
}

const TEMPLATES = Object.keys(TEMPLATE_DEFINITIONS)

const DEFAULT_CHECKLIST_ITEMS = [
  { id: 1, text: 'مسارات الهروب وأبواب الطوارئ خالية تماماً من أية عوائق أو مواد مخزنة', status: 'PASS' },
  { id: 2, text: 'التزام جميع العاملين بارتداء مهمات الوقاية الشخصية (PPE) المقررة بالمنطقة', status: 'PASS' },
  { id: 3, text: 'معدات الإطفاء صالحة، ومؤشرات الضغط في النطاق الأخضر مع سلامة خراطيمها', status: 'PASS' },
  { id: 4, text: 'اللوحات الكهربائية مغلقة ومحمية وتوجد مسافة أمان لا تقل عن متر أمامها', status: 'PASS' },
  { id: 5, text: 'التخزين السليم للمواد وخلو الأرضيات والممرات من أية تسريبات زيوت أو شحوم', status: 'PASS' },
  { id: 6, text: 'تصاريح العمل السارية (PTW) معلقة وواضحة بموقع الأعمال ذات الخطورة', status: 'PASS' },
]

export default function Inspections() {
  const toast = useToast()
  const stats = useApi(() => inspApi.stats(), [])
  const schedule = useApi(() => inspApi.schedule(), [])
  const findings = useApi(() => inspApi.findings(), [])
  const templates = useApi(() => inspApi.templates(), [])

  // Toggle Tab for the right-side card: 'findings' vs 'walks'
  const [activeNotesTab, setActiveNotesTab] = useState('findings')

  // Selected inspection walk for full details view modal
  const [selectedWalk, setSelectedWalk] = useState(null)

  // Optimistic local state
  const [newSchedules, setNewSchedules] = useState([])
  const [newFindings, setNewFindings] = useState([])

  const reloadAll = () => {
    stats.reload?.()
    schedule.reload?.()
    findings.reload?.()
    templates.reload?.()
  }

  // Subscribe to live database changes from AI Assistant mutations
  useEffect(() => {
    const handleDataChanged = (e) => {
      const entity = e?.detail?.entity || ''
      if (!entity || entity.includes('inspect') || entity.includes('finding') || entity === 'all') {
        reloadAll()
      }
    }
    window.addEventListener('hse:data-changed', handleDataChanged)
    return () => window.removeEventListener('hse:data-changed', handleDataChanged)
  }, [])

  // Combined Schedule (All inspection rounds)
  const displaySchedule = useMemo(() => {
    const serverRows = Array.isArray(schedule.data) ? schedule.data : []
    const newItems = newSchedules.filter((n) => !serverRows.some((s) => s.id && s.id === n.id))
    return [...newItems, ...serverRows]
  }, [schedule.data, newSchedules])

  // Combined Findings
  const displayFindings = useMemo(() => {
    const serverRows = Array.isArray(findings.data) ? findings.data : []
    const newItems = newFindings.filter((n) => !serverRows.some((s) => s.title === n.title))
    return [...newItems, ...serverRows]
  }, [findings.data, newFindings])

  // --- 1. Schedule Modal State ---
  const [scheduleOpen, setScheduleOpen] = useState(false)
  const [schedForm, setSchedForm] = useState({
    type: 'تفتيش السلامة الأسبوعي لمصنع الكابلات',
    zone: 'خطوط العزل CCV',
    frequency: 'أسبوعي',
    owner: 'م. مصطفى (مدير السلامة)',
    next: getLocalDateString(new Date(Date.now() + 86400000)),
    template: 'ISO 45001 — تدقيق السلامة والصحة المهنية',
    notes: '',
  })
  const [schedSubmitting, setSchedSubmitting] = useState(false)

  const handleCreateSchedule = async (e) => {
    e.preventDefault()
    if (!schedForm.type || !schedForm.zone) {
      toast('يرجى تحديد نوع الجولة والمنطقة المستهدفة', 'wn')
      return
    }

    const tempItem = {
      id: Date.now(),
      type: schedForm.type,
      zone: schedForm.zone,
      frequency: schedForm.frequency,
      owner: schedForm.owner,
      next: schedForm.next,
      status: 'مجدول',
      tone: 'in',
      notes: schedForm.notes || 'جولة تفتيش مجدولة دورية',
      isNew: true,
    }

    setNewSchedules((prev) => [tempItem, ...prev])
    setSchedSubmitting(true)

    try {
      const res = await inspApi.createSchedule(schedForm)
      if (res?.data?.id) tempItem.id = res.data.id
      toast('تمت جدولة جولة التفتيش بنجاح وحفظها في قاعدة البيانات', 'ok')
      setScheduleOpen(false)
      reloadAll()
    } catch (err) {
      toast(err.message || 'تعذر حفظ الجولة المجدولة', 'cr')
    } finally {
      setSchedSubmitting(false)
    }
  }

  // --- 2. Live Walk Modal State ---
  const [walkOpen, setWalkOpen] = useState(false)
  const [walkForm, setWalkForm] = useState({
    type: 'تفتيش السلامة الميداني الشامل',
    zone: 'خطوط العزل CCV',
    inspector: 'م. مصطفى (مدير السلامة)',
    template: 'ISO 45001 — تدقيق السلامة والصحة المهنية',
    notes: '',
  })
  const [checklist, setChecklist] = useState(DEFAULT_CHECKLIST_ITEMS)
  const [findingForm, setFindingForm] = useState({
    title: '',
    category: 'بيئة العمل والسلامة الميدانية',
    grade: 'MAJOR',
  })
  const [hasCustomFinding, setHasCustomFinding] = useState(false)
  const [walkSubmitting, setWalkSubmitting] = useState(false)

  const handleToggleChecklist = (id, newStatus) => {
    const updated = checklist.map((item) => (item.id === id ? { ...item, status: newStatus } : item))
    setChecklist(updated)
    const anyFailed = updated.some((it) => it.status === 'FAIL')
    if (anyFailed && !hasCustomFinding) {
      const failedItem = updated.find((it) => it.status === 'FAIL')
      setFindingForm((prev) => ({
        ...prev,
        title: prev.title || `رصد عدم مطابقة: ${failedItem?.text.slice(0, 45)}...`,
      }))
      setHasCustomFinding(true)
    }
  }

  const totalScored = checklist.filter((i) => i.status !== 'NA').length
  const passCount = checklist.filter((i) => i.status === 'PASS').length
  const calculatedScore = totalScored > 0 ? Math.round((passCount / totalScored) * 100) : 100

  const handleSubmitWalk = async (e) => {
    e.preventDefault()
    setWalkSubmitting(true)

    const walkFindings = []
    if (hasCustomFinding && findingForm.title.trim()) {
      const newF = {
        title: findingForm.title.trim(),
        category: findingForm.category,
        grade: findingForm.grade,
        state: 'مفتوح',
        color: findingForm.grade === 'CRITICAL' ? tc.crit() : findingForm.grade === 'MAJOR' ? tc.warn() : tc.info(),
        meta: `${findingForm.category} · المسؤول: ${walkForm.inspector} · الموعد: اليوم`,
      }
      walkFindings.push(newF)
      setNewFindings((prev) => [newF, ...prev])
    }

    const finalNotes = walkForm.notes || 'تم استكمال الجولة الميدانية وتسجيل نتائج الفحص بنجاح'

    const optimisticWalk = {
      id: Date.now(),
      type: walkForm.type,
      zone: walkForm.zone,
      frequency: 'أسبوعي',
      owner: walkForm.inspector,
      next: getLocalDateString(new Date()),
      status: 'مكتمل',
      tone: 'ok',
      score: calculatedScore,
      notes: finalNotes,
      isNew: true,
    }
    setNewSchedules((prev) => [optimisticWalk, ...prev])

    try {
      await inspApi.submitWalk({
        type: walkForm.type,
        zone: walkForm.zone,
        inspector: walkForm.inspector,
        template: walkForm.template,
        notes: finalNotes,
        score: calculatedScore,
        findings: walkFindings,
      })

      toast(`تم اعتماد الجولة بنجاح بنسبة التزام ${calculatedScore}% وحفظ الملاحظات`, 'ok')
      setWalkOpen(false)
      setChecklist(DEFAULT_CHECKLIST_ITEMS)
      setHasCustomFinding(false)
      setFindingForm({ title: '', category: 'بيئة العمل والسلامة الميدانية', grade: 'MAJOR' })
      setActiveNotesTab('walks') // Automatically switch to walks view so user sees their note immediately!
      reloadAll()
    } catch (err) {
      toast(err.message || 'تعذر اعتماد الجولة الميدانية', 'cr')
    } finally {
      setWalkSubmitting(false)
    }
  }

  // --- 3. Interactive Finding Detail & Action Modal ---
  const [selectedFinding, setSelectedFinding] = useState(null)
  const [findingActionNotes, setFindingActionNotes] = useState('')
  const [updatingFinding, setUpdatingFinding] = useState(false)

  const handleUpdateFindingStatus = async (newStatus) => {
    if (!selectedFinding) return
    setUpdatingFinding(true)
    try {
      if (selectedFinding.id) {
        await inspApi.updateFindingStatus(selectedFinding.id, {
          state: newStatus,
          notes: findingActionNotes,
        })
      }
      setNewFindings((prev) =>
        prev.map((f) => (f.title === selectedFinding.title ? { ...f, state: newStatus } : f))
      )
      toast(`تم تحديث حالة الملاحظة إلى "${newStatus}" بنجاح`, 'ok')
      setSelectedFinding(null)
      setFindingActionNotes('')
      reloadAll()
    } catch (err) {
      toast(err.message || 'تعذر تحديث حالة الملاحظة', 'cr')
    } finally {
      setUpdatingFinding(false)
    }
  }

  // --- 4. Mobile QR Scanner Simulation Modal ---
  const [qrModalOpen, setQrModalOpen] = useState(false)
  const [qrScanning, setQrScanning] = useState(false)
  const [qrChecklist, setQrChecklist] = useState({
    present: true,
    pressureOk: true,
    hoseOk: true,
    pinSealOk: true,
    accessClear: true,
    tagUpdated: true,
  })
  const [qrNotes, setQrNotes] = useState('')
  const [qrSubmitting, setQrSubmitting] = useState(false)

  const handleStartQrScan = () => {
    setQrScanning(true)
    setQrModalOpen(true)
    setTimeout(() => {
      setQrScanning(false)
    }, 900)
  }

  const handleSubmitQrInspection = async () => {
    setQrSubmitting(true)
    try {
      const allPassed = Object.values(qrChecklist).every(Boolean)
      try {
        await fireApi.createInspection({
          equipmentTag: 'FE-A-014',
          zone: 'خط الإنتاج A',
          pass: allPassed,
          notes: qrNotes || 'تم فحص المعدة عبر مسح الـ QR الميداني وتأكيد مطابقتها',
        })
      } catch (ignored) {}

      toast('تم تسجيل فحص المعدة (QR-FE-A-014) واعتماده في سجلات السلامة', 'ok')
      setQrModalOpen(false)
      reloadAll()
    } catch (err) {
      toast(err.message || 'تعذر حفظ الفحص', 'cr')
    } finally {
      setQrSubmitting(false)
    }
  }

  // --- 5. Template Preview & Form Builder Modal ---
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [selectedFieldType, setSelectedFieldType] = useState(null)

  const handleOpenTemplate = (templateName) => {
    const def = TEMPLATE_DEFINITIONS[templateName] || {
      name: templateName,
      authority: 'ESCA Safety Standards',
      itemCount: 20,
      category: 'معيار مخصص',
      items: DEFAULT_CHECKLIST_ITEMS.map((i) => i.text),
    }
    setSelectedTemplate(def)
  }

  const handleApplyTemplateToWalk = (tpl) => {
    setSelectedTemplate(null)
    const newItems = (tpl.items || []).slice(0, 6).map((text, idx) => ({
      id: idx + 1,
      text,
      status: 'PASS',
    }))
    setChecklist(newItems.length > 0 ? newItems : DEFAULT_CHECKLIST_ITEMS)
    setWalkForm((prev) => ({
      ...prev,
      type: tpl.name,
      template: tpl.name,
    }))
    setWalkOpen(true)
    toast(`تم تطبيق قالب "${tpl.name}" وتجهيز بنود الفحص الميداني`, 'ok')
  }

  return (
    <>
      <PageHeader title="التفتيش والجولات" meta="inspection & safety walks">
        <Btn
          variant="sec"
          icon="bot"
          onClick={() => {
            window.dispatchEvent(
              new CustomEvent('hse:open-assistant', {
                detail: {
                  prompt: 'ما هي إحصائيات ونسبة الامتثال لجولات التفتيش واقتراحات الفحص القادم؟',
                  autoSend: true,
                },
              })
            )
          }}
        >
          مساعد التفتيش الذكي AI
        </Btn>
        <Btn icon="calendar" onClick={() => setScheduleOpen(true)}>
          جدولة جولة
        </Btn>
        <Btn variant="pri" icon="inspection" onClick={() => setWalkOpen(true)}>
          بدء جولة تفتيش
        </Btn>
      </PageHeader>

      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="جولات مكتملة" value={s.completed} tone="safe" sub={`من ${s.planned} مخططة`} />
            <Kpi label="ملاحظات مفتوحة" value={s.openFindings} tone="warn" sub={`${s.overdueFindings} متأخرة عن الموعد`} />
            <Kpi label="نسبة الالتزام" value={`${s.compliance}%`} tone="info" sub="الهدف ≥ 95%" />
            <Kpi label="جولات متأخرة" value={s.overdueWalks} tone="crit" sub="ورشة الصيانة · المرافق" />
          </KpiRow>
        )}
      </Async>

      <Grid cols={2}>
        {/* SCHEDULE TABLE */}
        <Card>
          <CardHead title="جدول الجولات" hint="SCHEDULE">
            <span className="text-2xs font-mono text-txt-3 bg-steel px-2 py-0.5 rounded">
              {displaySchedule.length} جولة مسجلة
            </span>
          </CardHead>
          <Async state={schedule} rows={8}>
            {() => (
              <Table head={['النوع', 'المنطقة', 'التكرار', 'المسؤول', 'القادمة', 'الحالة']} clickable={false}>
                {displaySchedule.map((r, i) => (
                  <tr
                    key={r.id ? `sched-${r.id}` : `${r.type}-${r.zone}-${i}`}
                    onClick={() => setSelectedWalk(r)}
                    className={`cursor-pointer hover:bg-steel/60 transition-colors ${
                      r.isNew ? 'bg-hi/5 font-medium' : ''
                    }`}
                  >
                    <td className="font-semibold text-txt-1">
                      {r.type}
                      {r.isNew && (
                        <span className="ms-1.5 inline-block text-[10px] bg-hi/20 text-hi px-1.5 py-0.2 rounded font-mono">
                          جديد
                        </span>
                      )}
                    </td>
                    <td className="text-xs text-txt-2">{r.zone}</td>
                    <td className="text-xs">{r.frequency || 'أسبوعي'}</td>
                    <td className="text-xs">{r.owner}</td>
                    <td className="mono">{r.next}</td>
                    <td>
                      <Pill tone={r.tone}>{r.status}</Pill>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>

        {/* TOGGLEABLE CARD: FINDINGS vs ALL INSPECTIONS & NOTES */}
        <Card>
          <CardHead
            title={
              activeNotesTab === 'findings'
                ? 'ملاحظات عدم المطابقة (Findings)'
                : 'سجل وتوصيات جولات التفتيش'
            }
            hint={activeNotesTab === 'findings' ? 'LIVE FINDINGS' : 'INSPECTION NOTES'}
          >
            {/* View Mode Toggle Switch */}
            <div className="flex items-center bg-steel rounded-md p-0.5 border border-line">
              <button
                type="button"
                onClick={() => setActiveNotesTab('findings')}
                className={`text-2xs px-2.5 py-1 rounded transition-all font-semibold ${
                  activeNotesTab === 'findings'
                    ? 'bg-hi text-white shadow-sm'
                    : 'text-txt-3 hover:text-txt-1'
                }`}
              >
                ملاحظات السلامة ({displayFindings.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveNotesTab('walks')}
                className={`text-2xs px-2.5 py-1 rounded transition-all font-semibold ${
                  activeNotesTab === 'walks'
                    ? 'bg-hi text-white shadow-sm'
                    : 'text-txt-3 hover:text-txt-1'
                }`}
              >
                سجل وتوصيات الجولات ({displaySchedule.length})
              </button>
            </div>
          </CardHead>

          <CardBody>
            {activeNotesTab === 'findings' ? (
              /* TAB 1: SAFETY FINDINGS TIMELINE */
              <Async state={findings} rows={6}>
                {() => (
                  <Timeline>
                    {displayFindings.map((f, i) => (
                      <TimelineItem
                        key={f.title + i}
                        time={`${f.grade}${f.state ? ` · ${f.state}` : ''}`}
                        color={f.color}
                      >
                        <div
                          onClick={() => setSelectedFinding(f)}
                          className="cursor-pointer p-1.5 -m-1.5 rounded hover:bg-steel/60 transition-all group"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <b className="font-semibold text-txt-1 group-hover:text-hi transition-colors">{f.title}</b>
                            <span className="text-2xs text-txt-3 opacity-0 group-hover:opacity-100 transition-opacity font-mono">
                              معاينة / تعديل ↗
                            </span>
                          </div>
                          <span className="text-txt-2 text-xs leading-relaxed block mt-0.5">{f.meta}</span>
                        </div>
                      </TimelineItem>
                    ))}
                  </Timeline>
                )}
              </Async>
            ) : (
              /* TAB 2: INSPECTION WALKS & NOTES LIST */
              <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
                {displaySchedule.map((walk, idx) => (
                  <div
                    key={walk.id ? `walk-card-${walk.id}` : `walk-${idx}`}
                    onClick={() => setSelectedWalk(walk)}
                    className="p-3 bg-steel/50 hover:bg-steel rounded-lg border border-line hover:border-hi/40 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-txt-1 group-hover:text-hi transition-colors">
                          {walk.type}
                        </span>
                        {walk.isNew && (
                          <span className="text-[10px] bg-hi/20 text-hi px-1.5 py-0.2 rounded font-mono">
                            جديد
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5">
                        {walk.score !== null && walk.score !== undefined && (
                          <span
                            className={`text-2xs font-mono font-bold px-1.5 py-0.5 rounded ${
                              Number(walk.score) >= 90
                                ? 'bg-safe/20 text-safe'
                                : Number(walk.score) >= 75
                                ? 'bg-warn/20 text-warn'
                                : 'bg-crit/20 text-crit'
                            }`}
                          >
                            {walk.score}%
                          </span>
                        )}
                        <Pill tone={walk.tone}>{walk.status}</Pill>
                      </div>
                    </div>

                    <div className="text-2xs text-txt-3 flex flex-wrap items-center gap-x-3 gap-y-1 mb-2 font-mono">
                      <span>📍 {walk.zone}</span>
                      <span>👤 {walk.owner}</span>
                      <span>📅 {walk.next}</span>
                    </div>

                    {/* Inspector Note Box */}
                    <div className="p-2.5 rounded bg-steel-2 border border-line/60 text-xs text-txt-2 leading-relaxed flex items-start gap-2">
                      <Icon name="inspection" size={14} className="text-hi shrink-0 mt-0.5" />
                      <div>
                        <span className="text-2xs text-txt-3 block font-semibold mb-0.5">ملاحظات وتوصيات الجولة:</span>
                        <p className="text-txt-1 font-normal italic">
                          "{walk.notes || 'تمت الجولة بنجاح وتوثيق مطابقة اشتراطات السلامة'}"
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </Grid>

      <Grid cols={2} className="mt-3.5">
        {/* MOBILE INSPECTION & QR SCAN */}
        <Card>
          <CardHead title="المفتش الميداني" hint="MOBILE INSPECTION" />
          <CardBody>
            <Async state={stats} rows={6}>
              {(s) => (
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <StatLine
                      label="وضع عدم الاتصال (Offline)"
                      value={<Pill tone="ok">مفعّل</Pill>}
                    />
                    <StatLine label="جولات مخزّنة محلياً" value={s.field?.cachedWalks ?? 3} />
                    <StatLine label="آخر مزامنة" value={s.field?.lastSync ?? '13:50'} />
                    <StatLine label="QR / NFC Tags" value={`${s.field?.tags ?? 182} tag`} />
                    <StatLine label="Geofencing" value={<Pill tone="ok">إلزامي</Pill>} />
                    <StatLine label="مسح مؤكد بالموقع" value={`${s.field?.verifiedScans ?? 98.4}%`} valueClass="text-safe" />
                  </div>
                  <div className="bg-steel border border-line rounded-md p-3.5 text-center flex flex-col justify-center">
                    <Icon name="qr" size={44} className="mx-auto mb-2 text-txt-2" />
                    <div className="font-mono num text-xs text-txt-2">QR-FE-A-014</div>
                    <p className="text-xs text-txt-3 mt-1.5 leading-7">
                      مسح الكود يفتح نموذج فحص المعدة ويسجّل الموقع والوقت تلقائياً
                    </p>
                    <Btn
                      size="sm"
                      variant="pri"
                      icon="qr"
                      className="mt-2.5 w-full justify-center"
                      onClick={handleStartQrScan}
                    >
                      محاكاة مسح الكود
                    </Btn>
                  </div>
                </div>
              )}
            </Async>
            <p className="mt-3.5 pt-3 border-t border-line text-xs text-txt-2 leading-7">
              النظام يرفض تسجيل الفحص إذا كان المفتش خارج نطاق <b className="font-mono num">15م</b> من موقع المعدة —
              لمنع الفحص الصوري (Pencil Whipping).
            </p>
          </CardBody>
        </Card>

        {/* FORM BUILDER & TEMPLATES */}
        <Card>
          <CardHead title="بانى نماذج التفتيش" hint="FORM BUILDER & STANDARDS" />
          <CardBody>
            <div className="flex items-center justify-between mb-2">
              <div className="text-[12.5px] font-semibold">أنواع الحقول المتاحة (انقر للمعاينة)</div>
            </div>
            <div className="mb-3.5 flex flex-wrap gap-1.5">
              {FIELD_TYPES.map((f) => (
                <button
                  type="button"
                  key={f.name}
                  onClick={() => setSelectedFieldType(f)}
                  className="text-xs px-2.5 py-1 rounded bg-steel hover:bg-hi/20 hover:text-hi border border-line transition-all text-txt-2"
                >
                  {f.name}
                </button>
              ))}
            </div>

            <div className="flex items-center justify-between mb-2">
              <div className="text-[12.5px] font-semibold">قوالب جاهزة حسب المعايير الدولية (انقر للاستعراض)</div>
            </div>
            <Async state={templates} rows={7}>
              {(rows) =>
                rows.map((t) => (
                  <div
                    key={t.name}
                    onClick={() => handleOpenTemplate(t.name)}
                    className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-steel/70 cursor-pointer transition-colors group"
                  >
                    <span className="text-xs text-txt-1 group-hover:text-hi font-medium flex items-center gap-1.5">
                      <Icon name="check" size={13} className="text-txt-3 group-hover:text-hi" />
                      {t.name}
                    </span>
                    <span className="text-2xs font-mono text-txt-3 group-hover:text-txt-1 bg-steel px-2 py-0.5 rounded">
                      {t.items} بند ↗
                    </span>
                  </div>
                ))
              }
            </Async>
          </CardBody>
        </Card>
      </Grid>

      {/* =============================================================== */}
      {/* 1. SCHEDULE INSPECTION MODAL                                     */}
      {/* =============================================================== */}
      <Modal
        open={scheduleOpen}
        onClose={() => setScheduleOpen(false)}
        title="جدولة جولة تفتيش جديدة"
        width={680}
        footer={
          <div className="flex justify-end gap-2 w-full">
            <Btn variant="ghost" onClick={() => setScheduleOpen(false)}>
              إلغاء
            </Btn>
            <Btn variant="pri" icon="check" onClick={handleCreateSchedule} disabled={schedSubmitting}>
              {schedSubmitting ? 'جاري الجدولة...' : 'حفظ وجدولة الجولة'}
            </Btn>
          </div>
        }
      >
        <form onSubmit={handleCreateSchedule} className="space-y-3.5">
          <Field label="نوع الجولة والتفتيش *">
            <select
              className="field"
              value={schedForm.type}
              onChange={(e) => setSchedForm({ ...schedForm, type: e.target.value })}
            >
              <option value="تفتيش السلامة الأسبوعي لمصنع الكابلات">تفتيش السلامة الأسبوعي لمصنع الكابلات</option>
              <option value="تدقيق أنظمة الإطفاء والإنذار المبكر">تدقيق أنظمة الإطفاء والإنذار المبكر</option>
              <option value="فحص مهمات الوقاية الشخصية (PPE)">فحص مهمات الوقاية الشخصية (PPE)</option>
              <option value="فحص ممرات ومعدات المستودعات والرافعات">فحص ممرات ومعدات المستودعات والرافعات</option>
              <option value="تدقيق السلامة الكهربائية والمحولات">تدقيق السلامة الكهربائية والمحولات</option>
              <option value="فحص تخزين الكيماويات والمواد الخطرة">فحص تخزين الكيماويات والمواد الخطرة</option>
              <option value="تفتيش الترتيب والنظافة الصناعية 5S">تفتيش الترتيب والنظافة الصناعية 5S</option>
              <option value="جولة الإدارة العليا الشهرية (Leadership Walk)">جولة الإدارة العليا الشهرية (Leadership Walk)</option>
            </select>
          </Field>

          <Grid cols={2}>
            <Field label="المنطقة المستهدفة *">
              <select
                className="field"
                value={schedForm.zone}
                onChange={(e) => setSchedForm({ ...schedForm, zone: e.target.value })}
              >
                {ZONES.map((z) => (
                  <option key={z} value={z}>
                    {z}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="تكرار الجولة *">
              <select
                className="field"
                value={schedForm.frequency}
                onChange={(e) => setSchedForm({ ...schedForm, frequency: e.target.value })}
              >
                <option value="يومي">يومي (Daily)</option>
                <option value="أسبوعي">أسبوعي (Weekly)</option>
                <option value="نصف شهري">نصف شهري (Bi-Weekly)</option>
                <option value="شهري">شهري (Monthly)</option>
                <option value="ربع سنوي">ربع سنوي (Quarterly)</option>
              </select>
            </Field>
          </Grid>

          <Grid cols={2}>
            <Field label="المسؤول / قائد فريق التفتيش *">
              <select
                className="field"
                value={schedForm.owner}
                onChange={(e) => setSchedForm({ ...schedForm, owner: e.target.value })}
              >
                {INSPECTORS.map((insp) => (
                  <option key={insp} value={insp}>
                    {insp}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="تاريخ الجولة القادمة *">
              <input
                type="date"
                className="field"
                value={schedForm.next}
                onChange={(e) => setSchedForm({ ...schedForm, next: e.target.value })}
              />
            </Field>
          </Grid>

          <Field label="نموذج وقائمة الفحص المعتمدة">
            <select
              className="field"
              value={schedForm.template}
              onChange={(e) => setSchedForm({ ...schedForm, template: e.target.value })}
            >
              {TEMPLATES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </Field>

          <Field label="ملاحظات وتوجيهات خاصة بالجولة">
            <textarea
              rows={2}
              className="field"
              placeholder="مثال: التركيز على ممرات الرافعات والتأكد من صيانة لوحات الكهرباء..."
              value={schedForm.notes}
              onChange={(e) => setSchedForm({ ...schedForm, notes: e.target.value })}
            />
          </Field>
        </form>
      </Modal>

      {/* =============================================================== */}
      {/* 2. START INSPECTION WALK MODAL                                   */}
      {/* =============================================================== */}
      <Modal
        open={walkOpen}
        onClose={() => setWalkOpen(false)}
        title="تنفيذ جولة تفتيش ميدانية وتسجيل الفحص"
        width={740}
        footer={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <span className="text-xs text-txt-3">نسبة الامتثال المحسوبة:</span>
              <span
                className={`font-mono font-bold text-sm px-2 py-0.5 rounded ${
                  calculatedScore >= 90 ? 'bg-safe/20 text-safe' : calculatedScore >= 75 ? 'bg-warn/20 text-warn' : 'bg-crit/20 text-crit'
                }`}
              >
                {calculatedScore}%
              </span>
            </div>
            <div className="flex gap-2">
              <Btn variant="ghost" onClick={() => setWalkOpen(false)}>
                إلغاء
              </Btn>
              <Btn variant="pri" icon="check" onClick={handleSubmitWalk} disabled={walkSubmitting}>
                {walkSubmitting ? 'جاري الاعتماد...' : 'اعتماد وتسجيل الجولة'}
              </Btn>
            </div>
          </div>
        }
      >
        <form onSubmit={handleSubmitWalk} className="space-y-4">
          <Grid cols={3}>
            <Field label="المنطقة المستهدفة">
              <select
                className="field text-xs"
                value={walkForm.zone}
                onChange={(e) => setWalkForm({ ...walkForm, zone: e.target.value })}
              >
                {ZONES.map((z) => (
                  <option key={z} value={z}>
                    {z}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="المفتش المسؤول">
              <select
                className="field text-xs"
                value={walkForm.inspector}
                onChange={(e) => setWalkForm({ ...walkForm, inspector: e.target.value })}
              >
                {INSPECTORS.map((insp) => (
                  <option key={insp} value={insp}>
                    {insp}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="قائمة التحقق">
              <select
                className="field text-xs"
                value={walkForm.template}
                onChange={(e) => setWalkForm({ ...walkForm, template: e.target.value })}
              >
                {TEMPLATES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </Field>
          </Grid>

          {/* Checklist Execution Block */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-txt-1">بنود التفتيش الميداني والامتثال (Checklist Items):</span>
              <span className="text-2xs text-txt-3">انقر لتحديد حالة كل بند</span>
            </div>

            <div className="space-y-2 border border-line rounded-lg p-3 bg-steel/40">
              {checklist.map((item) => (
                <div
                  key={item.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded bg-steel-2 border border-line/60"
                >
                  <div className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-steel text-txt-2 text-2xs font-mono flex items-center justify-center shrink-0 mt-0.5">
                      {item.id}
                    </span>
                    <span className="text-xs text-txt-1 leading-relaxed">{item.text}</span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-center">
                    <button
                      type="button"
                      onClick={() => handleToggleChecklist(item.id, 'PASS')}
                      className={`text-2xs px-2.5 py-1 rounded transition-all font-semibold ${
                        item.status === 'PASS'
                          ? 'bg-safe text-white shadow-sm'
                          : 'bg-steel border border-line text-txt-3 hover:text-txt-1'
                      }`}
                    >
                      مطابق ✓
                    </button>
                    <button
                      type="button"
                      onClick={() => handleToggleChecklist(item.id, 'FAIL')}
                      className={`text-2xs px-2.5 py-1 rounded transition-all font-semibold ${
                        item.status === 'FAIL'
                          ? 'bg-crit text-white shadow-sm'
                          : 'bg-steel border border-line text-txt-3 hover:text-txt-1'
                      }`}
                    >
                      غير مطابق ✕
                    </button>
                    <button
                      type="button"
                      onClick={() => handleToggleChecklist(item.id, 'NA')}
                      className={`text-2xs px-2 py-1 rounded transition-all ${
                        item.status === 'NA'
                          ? 'bg-txt-3 text-steel-2 font-semibold'
                          : 'bg-steel border border-line text-txt-3 hover:text-txt-1'
                      }`}
                    >
                      لا ينطبق
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Finding Section */}
          <div className="border border-line rounded-lg p-3 bg-steel/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-txt-1 flex items-center gap-1.5">
                <Icon name="incident" size={14} className="text-warn" />
                تسجيل ملاحظة سلامة / عدم مطابقة (Safety Finding)
              </span>
              <label className="flex items-center gap-1.5 text-xs text-txt-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasCustomFinding}
                  onChange={(e) => setHasCustomFinding(e.target.checked)}
                  className="rounded"
                />
                إرفاق ملاحظة مع الجولة
              </label>
            </div>

            {hasCustomFinding && (
              <div className="space-y-2.5 pt-2 border-t border-line/60 animate-fade">
                <Field label="وصف الملاحظة / الخلل المرصود *">
                  <input
                    type="text"
                    className="field text-xs"
                    placeholder="مثال: انسداد مسار مخرج الطوارئ بكراتين فارغة في عنبر CCV"
                    value={findingForm.title}
                    onChange={(e) => setFindingForm({ ...findingForm, title: e.target.value })}
                  />
                </Field>

                <Grid cols={2}>
                  <Field label="تصنيف الملاحظة">
                    <select
                      className="field text-xs"
                      value={findingForm.category}
                      onChange={(e) => setFindingForm({ ...findingForm, category: e.target.value })}
                    >
                      <option value="بيئة العمل والسلامة الميدانية">بيئة العمل والسلامة الميدانية</option>
                      <option value="سلوكيات وممارسات العاملين">سلوكيات وممارسات العاملين (BBS)</option>
                      <option value="معدات ومسارات الإطفاء">معدات ومسارات الإطفاء</option>
                      <option value="سلامة ميكانيكية وحواجز أمان">سلامة ميكانيكية وحواجز أمان</option>
                      <option value="لوحات وتوصيلات كهربائية">لوحات وتوصيلات كهربائية</option>
                      <option value="تخزين مواد كيميائية">تخزين مواد كيميائية</option>
                    </select>
                  </Field>

                  <Field label="درجة الخطورة (Severity)">
                    <select
                      className="field text-xs"
                      value={findingForm.grade}
                      onChange={(e) => setFindingForm({ ...findingForm, grade: e.target.value })}
                    >
                      <option value="CRITICAL">حرجة (CRITICAL) — تتطلب إيقاف وتدخل فوري</option>
                      <option value="MAJOR">رئيسية (MAJOR) — تصحيح خلال 48 ساعة</option>
                      <option value="MINOR">ثانوية (MINOR) — إجراء تحسيني</option>
                    </select>
                  </Field>
                </Grid>
              </div>
            )}
          </div>

          <Field label="ملاحظات وتوصيات المفتش العامة">
            <textarea
              rows={2}
              className="field text-xs"
              placeholder="اكتب أية ملاحظات عامة حول التزام الوردية أو حالة الموقع..."
              value={walkForm.notes}
              onChange={(e) => setWalkForm({ ...walkForm, notes: e.target.value })}
            />
          </Field>
        </form>
      </Modal>

      {/* =============================================================== */}
      {/* 3. FINDING DETAIL & ACTION MODAL                                 */}
      {/* =============================================================== */}
      <Modal
        open={Boolean(selectedFinding)}
        onClose={() => setSelectedFinding(null)}
        title="تفاصيل وإجراءات ملاحظة السلامة"
        width={620}
        footer={
          <div className="flex items-center justify-between w-full">
            <Btn variant="ghost" onClick={() => setSelectedFinding(null)}>
              إغلاق
            </Btn>
            <div className="flex gap-2">
              {selectedFinding?.state !== 'مفتوح' && (
                <Btn
                  variant="ghost"
                  onClick={() => handleUpdateFindingStatus('مفتوح')}
                  disabled={updatingFinding}
                >
                  إعادة فتح
                </Btn>
              )}
              {selectedFinding?.state !== 'تحت المعالجة' && (
                <Btn
                  variant="ghost"
                  className="text-warn border-warn/30"
                  onClick={() => handleUpdateFindingStatus('تحت المعالجة')}
                  disabled={updatingFinding}
                >
                  وضع قيد المعالجة
                </Btn>
              )}
              {selectedFinding?.state !== 'مغلق' && (
                <Btn
                  variant="pri"
                  icon="check"
                  onClick={() => handleUpdateFindingStatus('مغلق')}
                  disabled={updatingFinding}
                >
                  اعتماد الحل وإغلاق الملاحظة
                </Btn>
              )}
            </div>
          </div>
        }
      >
        {selectedFinding && (
          <div className="space-y-4">
            <div className="p-3.5 bg-steel rounded-lg border border-line">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span
                  className="font-mono text-2xs px-2 py-0.5 rounded font-bold"
                  style={{
                    backgroundColor: `${selectedFinding.color || tc.warn()}22`,
                    color: selectedFinding.color || tc.warn(),
                  }}
                >
                  {selectedFinding.grade}
                </span>
                <Pill
                  tone={
                    selectedFinding.state === 'مغلق'
                      ? 'ok'
                      : selectedFinding.state === 'تحت المعالجة'
                      ? 'wn'
                      : 'cr'
                  }
                >
                  {selectedFinding.state || 'مفتوح'}
                </Pill>
              </div>
              <h4 className="text-sm font-semibold text-txt-1 leading-relaxed">
                {selectedFinding.title}
              </h4>
            </div>

            <Grid cols={2}>
              <div className="p-3 bg-steel/50 rounded border border-line/60">
                <span className="text-2xs text-txt-3 block mb-0.5">التصنيف والمسؤول</span>
                <span className="text-xs font-semibold text-txt-1">{selectedFinding.meta}</span>
              </div>
              <div className="p-3 bg-steel/50 rounded border border-line/60">
                <span className="text-2xs text-txt-3 block mb-0.5">موعد الإغلاق المستهدف</span>
                <span className="text-xs font-mono font-semibold text-txt-1">
                  {selectedFinding.dueDate || '2026-08-31'}
                </span>
              </div>
            </Grid>

            <Field label="ملاحظات الإجراء التصحيحي المتخذ (CAPA)">
              <textarea
                rows={2}
                className="field text-xs"
                placeholder="أدخل تفاصيل المعالجة الميدانية، رقم أمر العمل أو اسم المنفذ..."
                value={findingActionNotes}
                onChange={(e) => setFindingActionNotes(e.target.value)}
              />
            </Field>
          </div>
        )}
      </Modal>

      {/* =============================================================== */}
      {/* 4. INSPECTION WALK DETAILS & NOTES MODAL                         */}
      {/* =============================================================== */}
      <Modal
        open={Boolean(selectedWalk)}
        onClose={() => setSelectedWalk(null)}
        title="تقرير وتوصيات جولة التفتيش"
        width={640}
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-xs text-txt-3">
              رقم الجولة: #{selectedWalk?.id || '—'} · الحالة: {selectedWalk?.status}
            </span>
            <Btn variant="ghost" onClick={() => setSelectedWalk(null)}>
              إغلاق
            </Btn>
          </div>
        }
      >
        {selectedWalk && (
          <div className="space-y-4">
            <div className="p-3.5 bg-steel rounded-lg border border-line flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-txt-1">{selectedWalk.type}</h4>
                <div className="text-2xs text-txt-3 font-mono mt-1">
                  📍 {selectedWalk.zone} · 👤 المسؤول: {selectedWalk.owner}
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <Pill tone={selectedWalk.tone}>{selectedWalk.status}</Pill>
                {selectedWalk.score !== null && selectedWalk.score !== undefined && (
                  <span
                    className={`text-2xs font-mono font-bold px-2 py-0.5 rounded ${
                      Number(selectedWalk.score) >= 90
                        ? 'bg-safe/20 text-safe'
                        : Number(selectedWalk.score) >= 75
                        ? 'bg-warn/20 text-warn'
                        : 'bg-crit/20 text-crit'
                    }`}
                  >
                    نسبة الامتثال: {selectedWalk.score}%
                  </span>
                )}
              </div>
            </div>

            <Grid cols={2}>
              <div className="p-3 bg-steel/50 rounded border border-line/60">
                <span className="text-2xs text-txt-3 block mb-0.5">تاريخ وتوقيت الجولة</span>
                <span className="text-xs font-mono font-semibold text-txt-1">
                  {selectedWalk.next || selectedWalk.completedAt || '2026-08-24'}
                </span>
              </div>
              <div className="p-3 bg-steel/50 rounded border border-line/60">
                <span className="text-2xs text-txt-3 block mb-0.5">تكرار الجولة المعتمد</span>
                <span className="text-xs font-semibold text-txt-1">{selectedWalk.frequency || 'أسبوعي'}</span>
              </div>
            </Grid>

            {/* Note Display Box */}
            <div className="p-3.5 bg-steel-2 rounded-lg border border-hi/30 space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-hi">
                <Icon name="inspection" size={15} />
                <span>ملاحظات وتوصيات المفتش الميدانية الموثقة:</span>
              </div>
              <p className="text-xs text-txt-1 leading-relaxed whitespace-pre-wrap p-2 bg-steel/60 rounded border border-line/50">
                {selectedWalk.notes || 'تمت الجولة بنجاح واعتماد التزام الموقع بالمعايير المقررة.'}
              </p>
            </div>
          </div>
        )}
      </Modal>

      {/* =============================================================== */}
      {/* 5. MOBILE QR SCANNER & QUICK INSPECTION MODAL                     */}
      {/* =============================================================== */}
      <Modal
        open={qrModalOpen}
        onClose={() => setQrModalOpen(false)}
        title="فحص المعدة الميداني عبر مسح الـ QR والـ Geofencing"
        width={620}
        footer={
          !qrScanning && (
            <div className="flex items-center justify-between w-full">
              <span className="text-xs text-txt-3">الموقع: خط الإنتاج A (ضمن نطاق 15م ✓)</span>
              <div className="flex gap-2">
                <Btn variant="ghost" onClick={() => setQrModalOpen(false)}>
                  إلغاء
                </Btn>
                <Btn
                  variant="pri"
                  icon="check"
                  onClick={handleSubmitQrInspection}
                  disabled={qrSubmitting}
                >
                  {qrSubmitting ? 'جاري الاعتماد...' : 'اعتماد وتسجيل الفحص'}
                </Btn>
              </div>
            </div>
          )
        }
      >
        {qrScanning ? (
          <div className="py-10 text-center space-y-3 animate-pulse">
            <Icon name="qr" size={54} className="mx-auto text-hi" />
            <div className="text-sm font-semibold text-txt-1">جاري قراءة رمز الاستجابة السريعة والتحقق من GPS...</div>
            <div className="text-xs text-txt-3 font-mono">Verifying Geofence & Tag ID...</div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-3.5 bg-steel rounded-lg border border-safe/40 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded bg-safe/10 text-safe flex items-center justify-center font-mono font-bold text-xs">
                  QR ✓
                </div>
                <div>
                  <div className="text-xs font-semibold text-txt-1">مطفأة حريق بودرة جافة 6 كجم — كود: FE-A-014</div>
                  <div className="text-2xs text-txt-3 font-mono mt-0.5">Zone: Production Line A · Geofence Verified (3.2m)</div>
                </div>
              </div>
              <Pill tone="ok">موقع مؤكد</Pill>
            </div>

            <div className="space-y-2">
              <div className="text-xs font-semibold text-txt-1 mb-1">قائمة الفحص البصري الفوري:</div>

              {[
                { key: 'present', label: 'المعدة متواجدة في موقعها المخصص ومعلقة بشكل سليم' },
                { key: 'pressureOk', label: 'مؤشر مقياس الضغط في النطاق الأخضر السليم (14-17 bar)' },
                { key: 'hoseOk', label: 'سلامة خرطوم وقاذف الإطفاء وخلوه من أية شروخ أو انسداد' },
                { key: 'pinSealOk', label: 'مسمار وتيلة الأمان البلاستيكية سليمة ولم يتم التلاعب بها' },
                { key: 'accessClear', label: 'خلو مسار الوصول للمطفأة تماماً من العوائق لمسافة 1 متر' },
                { key: 'tagUpdated', label: 'بطاقة الفحص السنوية معلقة وواضحة ومطابقة للرقم التسلسلي' },
              ].map((chk) => (
                <label
                  key={chk.key}
                  className="flex items-center justify-between p-2.5 rounded bg-steel-2 border border-line/60 cursor-pointer hover:border-hi/50 transition-colors"
                >
                  <span className="text-xs text-txt-1">{chk.label}</span>
                  <input
                    type="checkbox"
                    checked={qrChecklist[chk.key]}
                    onChange={(e) =>
                      setQrChecklist({ ...qrChecklist, [chk.key]: e.target.checked })
                    }
                    className="w-4 h-4 rounded text-hi"
                  />
                </label>
              ))}
            </div>

            <Field label="ملاحظات المفتش">
              <input
                type="text"
                className="field text-xs"
                placeholder="حالة المعدة ممتازة، تم تنظيف السطح وتوثيق القراءة..."
                value={qrNotes}
                onChange={(e) => setQrNotes(e.target.value)}
              />
            </Field>
          </div>
        )}
      </Modal>

      {/* =============================================================== */}
      {/* 6. TEMPLATE PREVIEW & INSPECTOR MODAL                             */}
      {/* =============================================================== */}
      <Modal
        open={Boolean(selectedTemplate)}
        onClose={() => setSelectedTemplate(null)}
        title={selectedTemplate ? `استعراض نموذج: ${selectedTemplate.name}` : ''}
        width={680}
        footer={
          selectedTemplate && (
            <div className="flex items-center justify-between w-full">
              <span className="text-xs text-txt-3">المرجعية: {selectedTemplate.authority}</span>
              <div className="flex gap-2">
                <Btn variant="ghost" onClick={() => setSelectedTemplate(null)}>
                  إغلاق
                </Btn>
                <Btn
                  variant="pri"
                  icon="inspection"
                  onClick={() => handleApplyTemplateToWalk(selectedTemplate)}
                >
                  بدء جولة تفتيش بهذا النموذج 🚀
                </Btn>
              </div>
            </div>
          )
        }
      >
        {selectedTemplate && (
          <div className="space-y-3.5">
            <div className="p-3 bg-steel rounded border border-line flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-txt-1">{selectedTemplate.name}</span>
                <span className="text-2xs text-txt-3 block mt-0.5">{selectedTemplate.category}</span>
              </div>
              <Pill tone="info">{selectedTemplate.itemCount} بند معتمد</Pill>
            </div>

            <div>
              <div className="text-xs font-semibold text-txt-1 mb-2">عينة من بنود الفحص المعتمدة بالمعيار:</div>
              <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
                {selectedTemplate.items.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2.5 p-2 bg-steel-2 rounded border border-line/60 text-xs text-txt-1"
                  >
                    <span className="w-5 h-5 rounded-full bg-steel text-txt-3 font-mono text-2xs flex items-center justify-center shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="leading-relaxed">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* =============================================================== */}
      {/* 7. FIELD TYPE INFO MODAL                                         */}
      {/* =============================================================== */}
      <Modal
        open={Boolean(selectedFieldType)}
        onClose={() => setSelectedFieldType(null)}
        title={selectedFieldType ? `نوع الحقل: ${selectedFieldType.name}` : ''}
        width={480}
        footer={
          <div className="flex justify-end w-full">
            <Btn variant="ghost" onClick={() => setSelectedFieldType(null)}>
              إغلاق
            </Btn>
          </div>
        }
      >
        {selectedFieldType && (
          <div className="space-y-3 p-2">
            <div className="p-3 bg-steel rounded border border-line">
              <span className="text-xs font-semibold text-txt-1 block mb-1">الوظيفة في نماذج التفتيش:</span>
              <p className="text-xs text-txt-2 leading-relaxed">{selectedFieldType.desc}</p>
            </div>
            <div className="p-3 bg-steel-2 rounded border border-line/60">
              <span className="text-2xs text-txt-3 block mb-1">الاستخدام الميداني:</span>
              <span className="text-xs text-safe font-semibold">متاح ومدمج في محرك الاستمارات الميدانية ونظام التفتيش</span>
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}
