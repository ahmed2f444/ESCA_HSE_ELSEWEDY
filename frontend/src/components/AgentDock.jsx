import { useEffect, useRef, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import Icon from './Icon.jsx'
import MarkdownRenderer from './MarkdownRenderer.jsx'
import { assistant } from '../api/endpoints.js'
import { useAuth } from '../hooks.jsx'
import { useVoiceAssistant } from '../useVoiceAssistant.js'
import VoiceSoundWave from './VoiceSoundWave.jsx'

/**
 * Floating AI Safety Assistant Dock with modern glassmorphic aesthetics and model switching.
 */
export default function AgentDock() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [modelMode, setModelMode] = useState('auto') // 'groq' | 'local' | 'auto'
  const [messages, setMessages] = useState([
    {
      role: 'agent',
      text: 'مرحباً بك! أنا المساعد الذكي للسلامة والصحة المهنية (ESCA AI Assistant).\n\nكيف يمكنني مساعدتك اليوم في استعلام الحوادث، التصاريح، المخاطر، أو قراءات الحساسات الحية؟',
      timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
    },
  ])
  const [suggestions, setSuggestions] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const bodyRef = useRef(null)
  const textareaRef = useRef(null)

  const [showVoiceLangMenu, setShowVoiceLangMenu] = useState(false)

  const voice = useVoiceAssistant({
    onTranscript: (t) => {
      setDraft((prev) => (prev ? `${prev.trim()} ${t}` : t))
    },
    defaultLang: 'auto',
  })

  useEffect(() => {
    if (!open || suggestions.length) return
    assistant.suggestions().then(setSuggestions).catch(() => {})
  }, [open, suggestions.length])

  useEffect(() => {
    if (open) {
      setTimeout(() => textareaRef.current?.focus(), 150)
    }
  }, [open])

  useEffect(() => {
    const handleOpen = (e) => {
      setOpen(true)
      if (e?.detail?.prompt) {
        setDraft(e.detail.prompt)
        if (e.detail.autoSend) {
          send(e.detail.prompt)
        }
      }
    }
    window.addEventListener('hse:open-assistant', handleOpen)
    return () => window.removeEventListener('hse:open-assistant', handleOpen)
  }, [])

  // Dedicated container-only scroll to bottom
  const scrollToBottom = useCallback((behavior = 'smooth') => {
    if (bodyRef.current) {
      bodyRef.current.scrollTo({
        top: bodyRef.current.scrollHeight,
        behavior,
      })
    }
  }, [])

  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      scrollToBottom('smooth')
    })
    return () => cancelAnimationFrame(raf)
  }, [messages, busy, scrollToBottom])

  // Auto-expanding textarea height calculation
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    const minHeight = 38
    const maxHeight = 120
    const nextHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight)
    textarea.style.height = `${nextHeight}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [draft])

  async function send(question) {
    const q = (question ?? draft).trim()
    if (!q || busy) return
    setDraft('')
    if (textareaRef.current) {
      textareaRef.current.style.height = '38px'
      textareaRef.current.style.overflowY = 'hidden'
    }

    const timeNow = new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' })
    setMessages((m) => [...m, { role: 'user', text: q, timestamp: timeNow }])
    setBusy(true)

    try {
      const historyContext = messages.slice(-6).map((m) => ({
        role: m.role,
        text: m.text,
      }))
      const activeUserRole =
        user?.role ||
        user?.role_name ||
        (user?.username === 'mostafa'
          ? 'HSE_MANAGER'
          : user?.username === 'admin'
          ? 'ADMIN'
          : user?.username === 'department.manager' || user?.username === 'esca.user03'
          ? 'PRODUCTION_SUPERVISOR'
          : 'WORKER')
      const res = await assistant.ask(
        q, 
        historyContext, 
        modelMode, 
        activeUserRole, 
        user?.username || user?.employeeId || 'USR-DEV'
      )
      
      const cleanText = (res.answer || '')
        .replace(/<think>[\s\S]*?<\/think>/gi, '')
        .replace(/<think>[\s\S]*/gi, '')
        .replace(/<tool_call>[\s\S]*?<\/tool_call>/gi, '')
        .replace(/<tool_call>[\s\S]*/gi, '')
        .replace(/<function_call>[\s\S]*?<\/function_call>/gi, '')
        .replace(/<function_call>[\s\S]*/gi, '')
        .replace(/<function[=\s][\s\S]*?<\/function>/gi, '')
        .replace(/<function[=\s][\s\S]*/gi, '')
        .replace(/<parameter[=\s][\s\S]*?<\/parameter>/gi, '')
        .replace(/<parameter[=\s][\s\S]*/gi, '')
        .replace(/<\/?(?:tool_call|function_call|function|parameter|think)[^>]*>/gi, '')
        .trim()
      const cleanAnswer = cleanText || 'تم استخراج البيانات من قاعدة البيانات بنجاح.'

      // Check if any certificate, permit, incident, or safety action was executed by AI agent
      const toolCalls = res.tool_calls || res.tools || []
      if (toolCalls.length > 0) {
        // Trigger live re-fetch for notifications and database state
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
      }

      const certCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_certificate' ||
          t.name === 'create_certificate' ||
          t.name === 'create_training_certificate' ||
          t.tool === 'create_certificate'
      )
      if (certCall) {
        const args = certCall.args || certCall.arguments || {}
        const result = certCall.result || certCall.output || {}
        const empName = args.employee_name || result.employee || result.employee_name || 'موظف'
        const courseName = args.course_name || result.course || result.course_name || 'دورة تدريبية'
        const isExp = result.status === 'EXPIRED' || result.is_expired || result.live_notification_triggered

        const notifObj = {
          id: 'NTF-' + (result.notification_id || Date.now()),
          notificationId: result.notification_id || Date.now(),
          title: isExp
            ? `تنبيه أتمتة السلامة: انتهاء صلاحية شهادة ${empName}`
            : `توثيق واعتماد شهادة تدريبية: ${empName}`,
          body: isExp
            ? `انتهت صلاحية شهادة تدريب الموظف ${empName} لدورة (${courseName}) — تم إطلاق تنبيه السلامة الآلي (AUT-002).`
            : `تم توثيق واعتماد شهادة تدريب (${courseName}) للموظف ${empName} بنجاح في مصفوفة الكفاءة وتحديث سجلات السلامة.`,
          time: 'الآن (مباشر)',
          color: isExp ? 'var(--crit)' : 'var(--safe)',
          type: isExp ? 'AUTOMATION_CERTIFICATE_EXPIRY' : 'TRAINING',
          to: '/training',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      const inspCall = toolCalls.find(
        (t) =>
          t.tool_name === 'schedule_safety_inspection' ||
          t.name === 'schedule_safety_inspection' ||
          t.tool_name === 'submit_inspection_walk' ||
          t.name === 'submit_inspection_walk' ||
          t.tool_name === 'create_inspection_finding' ||
          t.name === 'create_inspection_finding' ||
          t.tool_name === 'update_inspection_status' ||
          t.name === 'update_inspection_status' ||
          t.tool_name === 'update_inspection' ||
          t.name === 'update_inspection' ||
          t.tool_name === 'delete_inspection' ||
          t.name === 'delete_inspection' ||
          t.tool_name === 'update_inspection_finding' ||
          t.name === 'update_inspection_finding' ||
          t.tool_name === 'delete_inspection_finding' ||
          t.name === 'delete_inspection_finding' ||
          t.tool_name === 'log_fire_inspection' ||
          t.name === 'log_fire_inspection' ||
          t.tool_name === 'service_fire_equipment' ||
          t.name === 'service_fire_equipment' ||
          t.tool_name === 'add_fire_equipment' ||
          t.name === 'add_fire_equipment' ||
          t.tool_name === 'update_fire_equipment' ||
          t.name === 'update_fire_equipment'
      )
      if (inspCall) {
        const tName = inspCall.tool_name || inspCall.name || ''
        const args = inspCall.args || inspCall.arguments || {}
        const result = inspCall.result || inspCall.output || {}
        const isDelete = tName.includes('delete')
        const isFinding = tName.includes('finding')
        const isFire = tName.includes('fire')
        const isService = tName.includes('service')

        const notifObj = {
          id: 'NTF-INSP-' + (result.inspection_id || result.work_order_id || result.finding_id || Date.now()),
          notificationId: result.inspection_id || result.finding_id || Date.now(),
          title: isDelete
            ? `حذف سجل #${result.inspection_id || result.finding_id || args.inspection_id || ''}`
            : isService
            ? `أمر شغل صيانة إطفاء (${result.work_order_id || 'WO-FIRE'}): ${result.equipment_tag || 'طفاية حريق'}`
            : isFire
            ? `فحص وتفتيش معدات الحريق: ${result.equipment_tag || args.equipment_tag || 'معدة إطفاء'}`
            : isFinding
            ? `ملاحظات التفتيش وعدم المطابقة (${args.category || result.category || 'ميدانية'})`
            : `جولات التفتيش: ${args.inspection_type || result.inspection_type || 'جولة سلامة'}`,
          body: result.message || `تم تنفيذ العملية بنجاح وتحديث لوحة جولات السلامة والتفتيش.`,
          time: 'الآن (مباشر)',
          color: isDelete ? 'var(--crit)' : isFinding ? 'var(--warn)' : 'var(--safe)',
          type: isFire ? 'FIRE_SAFETY' : 'INSPECTION',
          to: isFire ? '/fire-equipment' : '/inspections',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if PPE or Safety Equipment action was executed
      const ppeCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_ppe_supply_order' ||
          t.name === 'create_ppe_supply_order' ||
          t.tool_name === 'create_ppe_transaction' ||
          t.name === 'create_ppe_transaction' ||
          t.tool_name === 'delete_ppe_transaction' ||
          t.name === 'delete_ppe_transaction' ||
          t.tool_name === 'add_ppe_item' ||
          t.name === 'add_ppe_item' ||
          t.tool_name === 'update_ppe_item' ||
          t.name === 'update_ppe_item' ||
          t.tool_name === 'delete_ppe_item' ||
          t.name === 'delete_ppe_item' ||
          t.tool_name === 'update_ppe_stock' ||
          t.name === 'update_ppe_stock' ||
          t.tool_name === 'record_fixed_safety_asset_inspection' ||
          t.name === 'record_fixed_safety_asset_inspection'
      )
      if (ppeCall) {
        const tName = ppeCall.tool_name || ppeCall.name || ''
        const result = ppeCall.result || ppeCall.output || {}
        const args = ppeCall.args || ppeCall.arguments || {}
        const isOrder = tName.includes('supply_order')
        const isTx = tName.includes('transaction')
        const isFixed = tName.includes('fixed_safety')

        const notifObj = {
          id: 'NTF-PPE-' + (result.transaction_id || result.order_reference || result.ppe_item_id || Date.now()),
          notificationId: result.transaction_id || result.ppe_item_id || Date.now(),
          title: isOrder
            ? `طلب توريد مهمات الوقاية (${result.order_reference || 'PO-PPE'})`
            : isTx
            ? `حركة مهمات الوقاية: ${result.transaction_type_ar || 'صرف / إرجاع'}`
            : isFixed
            ? `فحص معدات السلامة: ${result.asset_name || 'معدة سلامة ثابتة'}`
            : `تحديث مخزون الوقاية: ${result.item_code || result.name_ar || 'صنف مهمة'}`,
          body: result.message || 'تم تحديث سجلات مهمات الوقاية الشخصية ومخزون السلامة بنجاح.',
          time: 'الآن (مباشر)',
          color: isOrder ? 'var(--info)' : 'var(--safe)',
          type: 'PPE',
          to: '/ppe',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if Incident / RCA / Export / Template / Dashboard action was executed
      const incCall = toolCalls.find(
        (t) =>
          t.tool_name === 'export_incidents_excel' ||
          t.name === 'export_incidents_excel' ||
          t.tool_name === 'generate_external_report_template' ||
          t.name === 'generate_external_report_template' ||
          t.tool_name === 'create_incident_rca' ||
          t.name === 'create_incident_rca' ||
          t.tool_name === 'create_incident' ||
          t.name === 'create_incident' ||
          t.tool_name === 'refresh_dashboard' ||
          t.name === 'refresh_dashboard'
      )
      if (incCall) {
        const tName = incCall.tool_name || incCall.name || ''
        const result = incCall.result || incCall.output || {}
        const isExport = tName.includes('export')
        const isTmpl = tName.includes('template')
        const isRca = tName.includes('rca')
        const isDash = tName.includes('dashboard')

        if (isExport) {
          window.dispatchEvent(new CustomEvent('hse:export-incidents', { detail: { rows: result.rows, summary: result.summary } }))
        }
        if (isTmpl) {
          window.dispatchEvent(new CustomEvent('hse:open-template-modal', { detail: { templateType: result.template_type, data: result } }))
        }
        if (isDash) {
          window.dispatchEvent(new CustomEvent('hse:refresh-dashboard'))
        }
        window.dispatchEvent(new CustomEvent('hse:data-changed'))

        const notifObj = {
          id: 'NTF-INC-' + (result.incident_id || result.rca_id || Date.now()),
          notificationId: result.incident_id || result.rca_id || Date.now(),
          title: isExport
            ? 'تصدير سجل الحوادث إلى ملف Excel'
            : isTmpl
            ? `توليد ${result.title || 'النموذج الرسمي'}`
            : isRca
            ? `تحليل السبب الجذري للحادث #${result.incident_id || 'INC'}`
            : isDash
            ? 'تحديث لوحة قيادة السلامة الحية'
            : `تسجيل بلاغ حادث جديد (${result.incident_id || 'INC'})`,
          body: result.message || 'تم تنفيذ العملية وتحديث سجلات السلامة بنجاح.',
          time: 'الآن (مباشر)',
          color: isExport ? 'var(--info)' : isDash ? 'var(--info)' : isRca ? 'var(--warn)' : 'var(--safe)',
          type: isDash ? 'DASHBOARD' : 'INCIDENT',
          to: isDash ? '/' : '/incidents',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if Reports & Analytics action was executed
      const reportCall = toolCalls.find(
        (t) =>
          t.tool_name === 'export_reports_excel' ||
          t.name === 'export_reports_excel' ||
          t.tool_name === 'export_reports_pdf' ||
          t.name === 'export_reports_pdf' ||
          t.tool_name === 'send_report_to_management' ||
          t.name === 'send_report_to_management' ||
          t.tool_name === 'generate_custom_report' ||
          t.name === 'generate_custom_report' ||
          t.tool_name === 'open_ready_report' ||
          t.name === 'open_ready_report' ||
          t.tool_name === 'schedule_report' ||
          t.name === 'schedule_report'
      )
      if (reportCall) {
        const tName = reportCall.tool_name || reportCall.name || ''
        const result = reportCall.result || reportCall.output || {}
        const args = reportCall.args || reportCall.arguments || {}

        const isExcel = tName === 'export_reports_excel'
        const isPdf = tName === 'export_reports_pdf'
        const isSend = tName === 'send_report_to_management'
        const isCustom = tName === 'generate_custom_report'
        const isReady = tName === 'open_ready_report'
        const isSched = tName === 'schedule_report'

        if (isExcel) {
          window.dispatchEvent(new CustomEvent('hse:export-reports-excel', { detail: result }))
        }
        if (isPdf) {
          window.dispatchEvent(new CustomEvent('hse:export-reports-pdf', { detail: result }))
        }
        if (isSend) {
          window.dispatchEvent(new CustomEvent('hse:send-management', { detail: { ...args, ...result, autoSubmit: true } }))
        }
        if (isCustom) {
          window.dispatchEvent(new CustomEvent('hse:open-custom-report-builder', { detail: result }))
        }
        if (isReady) {
          window.dispatchEvent(new CustomEvent('hse:open-ready-report', { detail: { reportId: result.report_id || args.report_id } }))
        }
        if (isSched) {
          window.dispatchEvent(new CustomEvent('hse:schedule-report', { detail: result }))
        }
        window.dispatchEvent(new CustomEvent('hse:data-changed'))

        const notifObj = {
          id: 'NTF-RPT-' + (result.dispatch_id || result.schedule_id || Date.now()),
          notificationId: result.dispatch_id || Date.now(),
          title: isExcel
            ? 'تصدير مصنف تقارير السلامة Excel'
            : isPdf
            ? 'تصدير / طباعة التقرير التنفيذي PDF'
            : isSend
            ? `إرسال ${result.report_type || 'التقرير التنفيذي'} للإدارة`
            : isCustom
            ? `توليد ${result.title || 'تقرير مخصص'}`
            : isReady
            ? `فحص ${result.title || 'التقرير الجاهز'}`
            : 'تفعيل جدولة تقرير السلامة الآلي',
          body: result.message || 'تمت أتمتة إجراء التقارير بنجاح وتحديث لوحة التحليلات.',
          time: 'الآن (مباشر)',
          color: isSend ? 'var(--pri)' : isPdf ? 'var(--info)' : isExcel ? 'var(--safe)' : 'var(--warn)',
          type: 'REPORTS_ANALYTICS',
          to: '/reports',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if Electronic Permit to Work (ePTW) / SIMOPS action was executed
      const permitCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_permit' ||
          t.name === 'create_permit' ||
          t.tool_name === 'update_permit_status' ||
          t.name === 'update_permit_status' ||
          t.tool_name === 'update_permit' ||
          t.name === 'update_permit' ||
          t.tool_name === 'delete_permit' ||
          t.name === 'delete_permit' ||
          t.tool_name === 'close_all_permits' ||
          t.name === 'close_all_permits' ||
          t.tool_name === 'delete_all_permits' ||
          t.name === 'delete_all_permits' ||
          t.tool_name === 'check_simops_conflicts' ||
          t.name === 'check_simops_conflicts'
      )
      if (permitCall) {
        const tName = permitCall.tool_name || permitCall.name || ''
        const result = permitCall.result || permitCall.output || {}
        const args = permitCall.args || permitCall.arguments || {}
        const isDelete = tName.includes('delete')
        const isSimops = tName.includes('simops')
        const pCode = result.permit_code || `PTW-${result.permit_id || args.permit_id || ''}`

        const notifObj = {
          id: 'NTF-PTW-' + (result.permit_id || Date.now()),
          notificationId: result.permit_id || Date.now(),
          title: isSimops
            ? `فحص تعارضات العمليات المتزامنة SIMOPS (${result.conflicts_count || 0} تعارض)`
            : isDelete
            ? `حذف / إلغاء تصريح العمل (${pCode})`
            : `تصريح عمل إلكتروني ePTW: ${pCode}`,
          body: result.message || 'تم تحديث سجل تصاريح العمل الإلكترونية ePTW وإدارة المخاطر بنجاح.',
          time: 'الآن (مباشر)',
          color: isDelete ? 'var(--crit)' : isSimops ? 'var(--warn)' : 'var(--safe)',
          type: 'PERMIT',
          to: '/permits',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if Risk Assessment (HIRA) action was executed
      const riskCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_risk_assessment' ||
          t.name === 'create_risk_assessment' ||
          t.tool_name === 'update_risk_assessment' ||
          t.name === 'update_risk_assessment'
      )
      if (riskCall) {
        const result = riskCall.result || riskCall.output || {}
        const args = riskCall.args || riskCall.arguments || {}
        const notifObj = {
          id: 'NTF-RISK-' + (result.risk_id || Date.now()),
          notificationId: result.risk_id || Date.now(),
          title: `تقييم المخاطر الميدانية (HIRA #${result.risk_id || ''})`,
          body: result.message || `تم تسجيل تقييم الخطر (${result.hazard || args.hazard || 'مخاطر تشغيلية'}) وتحديث مصفوفة المخاطر.`,
          time: 'الآن (مباشر)',
          color: result.risk_level === 'HIGH' || result.risk_level === 'CRITICAL' ? 'var(--crit)' : 'var(--warn)',
          type: 'RISK_ASSESSMENT',
          to: '/risk',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if Job Safety Analysis (JSA) action was executed
      const jsaCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_jsa' ||
          t.name === 'create_jsa' ||
          t.tool_name === 'update_jsa' ||
          t.name === 'update_jsa'
      )
      if (jsaCall) {
        const result = jsaCall.result || jsaCall.output || {}
        const args = jsaCall.args || jsaCall.arguments || {}
        const notifObj = {
          id: 'NTF-JSA-' + (result.jsa_id || Date.now()),
          notificationId: result.jsa_id || Date.now(),
          title: `تحليل سلامة المهام (JSA #${result.jsa_id || ''})`,
          body: result.message || `تم اعتماد وثيقة تحليل سلامة المهمة (${result.task_name || args.task_name || 'مهمة عمل'}) بنجاح.`,
          time: 'الآن (مباشر)',
          color: 'var(--safe)',
          type: 'JSA',
          to: '/jsa',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if HazMat / Chemicals action was executed
      const hazmatCall = toolCalls.find(
        (t) =>
          t.tool_name === 'add_chemical' ||
          t.name === 'add_chemical' ||
          t.tool_name === 'update_chemical' ||
          t.name === 'update_chemical' ||
          t.tool_name === 'update_chemical_stock' ||
          t.name === 'update_chemical_stock'
      )
      if (hazmatCall) {
        const result = hazmatCall.result || hazmatCall.output || {}
        const args = hazmatCall.args || hazmatCall.arguments || {}
        const notifObj = {
          id: 'NTF-HAZ-' + (result.chemical_id || Date.now()),
          notificationId: result.chemical_id || Date.now(),
          title: `سجل المواد الكيميائية والخطرة: ${result.trade_name || args.trade_name || 'مادة كيميائية'}`,
          body: result.message || 'تم تحديث بيانات صحيفة السلامة (MSDS) والتوافق الكيميائي للمادة بنجاح.',
          time: 'الآن (مباشر)',
          color: 'var(--warn)',
          type: 'HAZMAT',
          to: '/hazmat',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if Occupational Health / Medical Exam action was executed
      const healthCall = toolCalls.find(
        (t) =>
          t.tool_name === 'record_medical_exam' ||
          t.name === 'record_medical_exam' ||
          t.tool_name === 'schedule_medical_exam' ||
          t.name === 'schedule_medical_exam' ||
          t.tool_name === 'update_medical_exam' ||
          t.name === 'update_medical_exam'
      )
      if (healthCall) {
        const result = healthCall.result || healthCall.output || {}
        const args = healthCall.args || healthCall.arguments || {}
        const notifObj = {
          id: 'NTF-HLT-' + (result.exam_id || Date.now()),
          notificationId: result.exam_id || Date.now(),
          title: `الصحة المهنية والفحص الطبي: ${result.employee_name || args.employee_name || 'موظف'}`,
          body: result.message || 'تم توثيق نتيجة الفحص الطبي وتحديث سجل الكفاءة والملائمة الصحية.',
          time: 'الآن (مباشر)',
          color: result.fitness_result === 'UNFIT' ? 'var(--crit)' : 'var(--safe)',
          type: 'OCCUPATIONAL_HEALTH',
          to: '/occupational-health',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if AI Vision & IoT Monitoring action was executed
      const iotCall = toolCalls.find(
        (t) =>
          t.tool_name === 'add_iot_sensor' ||
          t.name === 'add_iot_sensor' ||
          t.tool_name === 'update_iot_sensor' ||
          t.name === 'update_iot_sensor' ||
          t.tool_name === 'log_ai_event' ||
          t.name === 'log_ai_event'
      )
      if (iotCall) {
        const result = iotCall.result || iotCall.output || {}
        const args = iotCall.args || iotCall.arguments || {}
        const notifObj = {
          id: 'NTF-IOT-' + (result.sensor_id || result.event_id || Date.now()),
          notificationId: result.sensor_id || result.event_id || Date.now(),
          title: `المراقبة الآلية والحساسات البيئية (${result.sensor_tag || args.sensor_tag || 'حساس ذكي'})`,
          body: result.message || 'تم تسجيل بيانات الحساس الذكي وتحديث منظومة المراقبة الآلية الحية.',
          time: 'الآن (مباشر)',
          color: 'var(--info)',
          type: 'IOT_MONITORING',
          to: '/ai-iot',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if CAPA action was executed
      const capaCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_capa' ||
          t.name === 'create_capa' ||
          t.tool_name === 'update_capa_status' ||
          t.name === 'update_capa_status'
      )
      if (capaCall) {
        const result = capaCall.result || capaCall.output || {}
        const args = capaCall.args || capaCall.arguments || {}
        const notifObj = {
          id: 'NTF-CAPA-' + (result.capa_id || Date.now()),
          notificationId: result.capa_id || Date.now(),
          title: `إجراء تصحيحي ووقائي (CAPA #${result.capa_id || ''})`,
          body: result.message || `تم تحديث خطة الإجراءات التصحيحية (${result.title || args.title || 'إجراء سلامة'}).`,
          time: 'الآن (مباشر)',
          color: 'var(--warn)',
          type: 'CAPA',
          to: '/reports',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      // Check if Master Data / Employee / Superuser action was executed
      const masterCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_employee' ||
          t.name === 'create_employee' ||
          t.tool_name === 'update_employee' ||
          t.name === 'update_employee' ||
          t.tool_name === 'delete_record' ||
          t.name === 'delete_record' ||
          t.tool_name === 'cancel_entity' ||
          t.name === 'cancel_entity' ||
          t.tool_name === 'execute_database_dml' ||
          t.name === 'execute_database_dml'
      )
      if (masterCall) {
        const tName = masterCall.tool_name || masterCall.name || ''
        const result = masterCall.result || masterCall.output || {}
        const args = masterCall.args || masterCall.arguments || {}
        const isDelete = tName.includes('delete') || tName.includes('cancel')
        const notifObj = {
          id: 'NTF-ADM-' + Date.now(),
          notificationId: Date.now(),
          title: isDelete
            ? `إجراء إداري: حذف / إلغاء سجل (${args.table_name || args.entity_type || 'قاعدة البيانات'})`
            : `البيانات المرجعية والموظفين: ${result.display_name || args.display_name || 'تحديث البيانات'}`,
          body: result.message || 'تم تحديث البيانات المركزية وقيد العملية في سجل التدقيق غير القابل للتعديل.',
          time: 'الآن (مباشر)',
          color: isDelete ? 'var(--crit)' : 'var(--safe)',
          type: 'MASTER_DATA',
          to: '/departments',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
      }

      setMessages((m) => [
        ...m,
        {
          role: 'agent',
          text: cleanAnswer || 'تم استخراج البيانات من قاعدة البيانات بنجاح.',
          tools: res.tool_calls || res.tools || [],
          model: res.model_used || (modelMode === 'local' ? 'Local Ollama' : 'Groq Online'),
          timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: 'agent',
          error: true,
          text: `تعذّر الاتصال بخدمة المساعد الذكي: ${e.message}`,
          timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } finally {
      setBusy(false)
      setTimeout(() => textareaRef.current?.focus(), 50)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (e.nativeEvent?.isComposing) return
      e.preventDefault()
      if (!busy && draft.trim()) {
        send()
      }
    }
  }

  return (
    <>
      {/* Floating Trigger Button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 end-6 z-[800] group flex items-center gap-3 bg-steel-2 hover:bg-steel-3 border border-line hover:border-hi/60 rounded-full ps-3.5 pe-5 py-2.5 text-xs font-semibold shadow-xl transition-all duration-200 hover:scale-105 active:scale-95"
        >
          <span className="relative flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-tr from-hi to-hi-2 text-white shadow-md">
            <Icon name="chat" size={16} />
            <span className="absolute -top-0.5 -end-0.5 w-2.5 h-2.5 rounded-full bg-safe border-2 border-steel-2" />
          </span>
          <div className="text-start">
            <div className="text-txt font-semibold leading-tight">المساعد الذكي للسلامة</div>
            <div className="text-[10px] text-txt-3 font-mono">AI SAFETY ASSISTANT</div>
          </div>
        </button>
      )}

      {/* Floating Chat Modal */}
      {open && (
        <section
          className="fixed bottom-6 end-6 z-[800] w-[min(480px,calc(100vw-2rem))] bg-steel-2 border border-line rounded-2xl flex flex-col overflow-hidden shadow-2xl animate-pop"
          style={{
            height: 'min(640px, calc(100vh - 5rem))',
          }}
        >
          {/* Header */}
          <header className="px-4 py-3 bg-steel-3/90 border-b border-line flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-tr from-hi to-hi-2 flex items-center justify-center text-white shadow-sm shrink-0">
                <Icon name="chat" size={16} />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xs sm:text-[13px] font-bold text-txt">المساعد الذكي للسلامة</h3>
                  <span className="px-1.5 py-0.5 rounded text-[9.5px] font-mono bg-safe/15 text-safe border border-safe/30">
                    ONLINE
                  </span>
                </div>
                <p className="text-[10px] text-txt-3 font-mono">ESCA Safety Assistant</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={voice.toggleAutoSpeak}
                title={voice.autoSpeak ? 'القراءة الصوتية التلقائية مفعلة (انقر للتعطيل)' : 'تفعيل القراءة الصوتية التلقائية'}
                className={`p-1.5 rounded-md transition-colors flex items-center gap-1 ${
                  voice.autoSpeak ? 'bg-safe/15 text-safe border border-safe/30' : 'text-txt-3 hover:text-txt hover:bg-steel-3'
                }`}
              >
                <Icon name={voice.autoSpeak ? 'volume' : 'volume-off'} size={15} />
              </button>
              <Link
                to="/ai-agent"
                onClick={() => setOpen(false)}
                title="فتح في صفحة كاملة"
                className="p-1.5 rounded-md text-txt-3 hover:text-txt hover:bg-steel-3 transition-colors"
              >
                <Icon name="external" size={15} />
              </Link>
              <button
                className="p-1.5 rounded-md text-txt-3 hover:text-crit hover:bg-steel-3 transition-colors"
                onClick={() => setOpen(false)}
                aria-label="إغلاق"
              >
                <Icon name="close" size={16} />
              </button>
            </div>
          </header>

          {/* Model Switcher Segmented Control */}
          <div className="px-3.5 py-2 bg-steel-3/60 border-b border-line flex items-center justify-between gap-1 text-[11px]">
            <span className="text-[10.5px] font-semibold text-txt-3 shrink-0">النموذج:</span>
            <div className="flex items-center gap-1 bg-steel-2 p-0.5 rounded-lg border border-line">
              <button
                type="button"
                onClick={() => setModelMode('groq')}
                className={`px-2 py-1 rounded text-[10.5px] font-semibold flex items-center gap-1 transition-all ${
                  modelMode === 'groq'
                    ? 'bg-hi text-white shadow-sm'
                    : 'text-txt-2 hover:text-txt'
                }`}
              >
                <Icon name="cloud" size={11} />
                <span>Groq Online</span>
              </button>
              <button
                type="button"
                onClick={() => setModelMode('local')}
                className={`px-2 py-1 rounded text-[10.5px] font-semibold flex items-center gap-1 transition-all ${
                  modelMode === 'local'
                    ? 'bg-safe text-white shadow-sm'
                    : 'text-txt-2 hover:text-txt'
                }`}
              >
                <Icon name="server" size={11} />
                <span>Ollama Local</span>
              </button>
              <button
                type="button"
                onClick={() => setModelMode('auto')}
                className={`px-2 py-1 rounded text-[10.5px] font-semibold flex items-center gap-1 transition-all ${
                  modelMode === 'auto'
                    ? 'bg-steel-3 text-txt shadow-sm border border-line'
                    : 'text-txt-2 hover:text-txt'
                }`}
              >
                <Icon name="bolt" size={11} />
                <span>تلقائي</span>
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div ref={bodyRef} className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div className="flex items-center gap-1.5 mb-1 px-1 text-[10px] text-txt-3 font-mono">
                  <span>{m.role === 'user' ? user?.displayName || user?.name || user?.username || 'أنت' : 'ESCA AI Agent'}</span>
                  {m.model && (
                    <>
                      <span>·</span>
                      <span className="text-info">{m.model}</span>
                    </>
                  )}
                  <span>·</span>
                  <span>{m.timestamp}</span>

                  {m.role === 'agent' && !m.error && (
                    <button
                      type="button"
                      onClick={() => voice.speak(m.text, m.id || i)}
                      title={voice.activeSpeakingId === (m.id || i) && voice.isSpeaking ? 'إيقاف الصوت' : 'استمع للإجابة'}
                      className="ms-1 p-0.5 rounded text-txt-3 hover:text-hi transition-colors flex items-center gap-1"
                    >
                      <Icon
                        name={voice.activeSpeakingId === (m.id || i) && voice.isSpeaking ? 'stop' : 'volume'}
                        size={12}
                      />
                      {voice.activeSpeakingId === (m.id || i) && voice.isSpeaking && (
                        <VoiceSoundWave isSpeaking={true} size="sm" />
                      )}
                    </button>
                  )}
                </div>

                <div
                  className={`rounded-xl p-3 text-xs leading-6 max-w-[88%] shadow-sm ${
                    m.role === 'user'
                      ? 'bg-hi text-white rounded-br-none whitespace-pre-wrap font-medium'
                      : m.error
                      ? 'bg-crit/15 border border-crit/40 text-crit rounded-bl-none whitespace-pre-wrap'
                      : 'bg-steel-3/90 border border-line text-txt-1 rounded-bl-none'
                  }`}
                >
                  {m.role === 'user' || m.error ? (
                    m.text
                  ) : (
                    <MarkdownRenderer content={m.text} />
                  )}
                </div>
              </div>
            ))}

            {busy && (
              <div className="flex flex-col items-start">
                <div className="bg-steel-3/90 border border-line rounded-xl p-3 text-xs text-txt-2 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-info animate-ping" />
                  <span className="text-[11.5px]">
                    جارٍ الاستعلام عبر{' '}
                    {modelMode === 'local'
                      ? 'Ollama المحلي'
                      : modelMode === 'groq'
                      ? 'Groq السحابي'
                      : 'المحرك الذكي'}
                    ...
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Quick suggestions if few messages */}
          {suggestions.length > 0 && messages.length <= 2 && (
            <div className="px-3.5 py-2 bg-steel-3/40 border-t border-line flex items-center gap-1.5 overflow-x-auto">
              <span className="text-[10px] font-semibold text-txt-3 shrink-0">مقترحات:</span>
              {suggestions.slice(0, 3).map((s, idx) => (
                <button
                  key={idx}
                  disabled={busy}
                  onClick={() => send(s)}
                  className="text-[10.5px] bg-steel-3 hover:bg-steel border border-line hover:border-hi/50 text-txt-2 hover:text-txt rounded-md px-2.5 py-1 whitespace-nowrap transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Live Voice Listening Banner */}
          {voice.isListening && (
            <div className="px-3.5 py-1.5 bg-crit/10 border-t border-crit/30 flex items-center justify-between text-xs text-crit animate-pulse">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-crit animate-ping" />
                <span className="font-semibold text-[11px]">
                  جارٍ الاستماع للصوت ({voice.availableLanguages?.find((l) => l.id === voice.langMode)?.label || 'تلقائي'})
                </span>
                <VoiceSoundWave isListening={true} size="sm" />
              </div>
              <span className="text-[10px] text-txt-3 font-mono">اضغط الميكروفون للإرسال</span>
            </div>
          )}

          {/* Live Transcribing Banner */}
          {voice.isTranscribing && (
            <div className="px-3.5 py-1.5 bg-hi/10 border-t border-hi/30 flex items-center justify-between text-xs text-hi animate-fade">
              <div className="flex items-center gap-2">
                <Icon name="refresh" size={12} className="animate-spin text-hi" />
                <span className="font-semibold text-[11px]">معالجة الصوت عبر Whisper...</span>
              </div>
              <span className="text-[10px] text-txt-3 font-mono">دقة متقدمة</span>
            </div>
          )}

          {/* Input Footer with Auto-Expanding Textarea & Voice Mic */}
          <div className="border-t border-line p-3 bg-steel-3/80">
            <div className="flex items-end gap-1.5 bg-steel-2 border border-line focus-within:border-hi/70 rounded-xl p-1.5 transition-all relative">
              {/* Unified Voice Control Group */}
              <div className="relative inline-flex items-center rounded-lg bg-steel-3 border border-line p-0.5 shrink-0 shadow-sm focus-within:border-hi/50">
                <button
                  type="button"
                  onClick={voice.toggleListening}
                  disabled={voice.isTranscribing}
                  title={voice.isListening ? 'إيقاف التسجيل الصوتي' : 'تحدث بالصوت'}
                  className={`h-7 px-2 rounded flex items-center gap-1 transition-all ${
                    voice.isListening
                      ? 'mic-btn-active text-white animate-pulse'
                      : voice.isTranscribing
                      ? 'bg-hi/20 text-hi cursor-wait'
                      : 'text-txt-2 hover:text-hi hover:bg-steel active:scale-95'
                  }`}
                  aria-label="تسجيل صوتي"
                >
                  {voice.isTranscribing ? (
                    <Icon name="refresh" size={13} className="animate-spin text-hi" />
                  ) : (
                    <Icon name="mic" size={13} />
                  )}
                </button>

                <div className="w-px h-4 bg-line mx-0.5" />

                <button
                  type="button"
                  onClick={() => setShowVoiceLangMenu((prev) => !prev)}
                  title="اختيار لغة أو لهجة التحدث"
                  className="h-7 px-1.5 rounded text-[10px] font-mono text-txt-3 hover:text-txt hover:bg-steel flex items-center gap-0.5 transition-colors"
                >
                  <span className="font-semibold">{voice.availableLanguages?.find((l) => l.id === voice.langMode)?.code || 'AUTO'}</span>
                  <Icon name="caret" size={8} className="text-txt-3" />
                </button>

                {showVoiceLangMenu && (
                  <div className="absolute bottom-9 right-0 w-56 bg-steel-3 border border-line rounded-xl p-1 shadow-2xl z-50 animate-scale-in">
                    <div className="px-2.5 py-1 text-[10px] font-semibold text-txt-3 border-b border-line mb-1">
                      لغة ولهجة الصوت
                    </div>
                    {voice.availableLanguages?.map((lang) => (
                      <button
                        key={lang.id}
                        type="button"
                        onClick={() => {
                          voice.changeLangMode(lang.id)
                          setShowVoiceLangMenu(false)
                        }}
                        className={`w-full text-right px-2.5 py-1.5 rounded-lg text-[11px] flex items-center justify-between transition-colors ${
                          voice.langMode === lang.id
                            ? 'bg-hi/15 text-hi font-semibold border border-hi/30'
                            : 'text-txt-2 hover:text-txt hover:bg-steel-2'
                        }`}
                      >
                        <span className="flex items-center gap-1.5">
                          <span className="font-mono text-[9px] px-1 py-0.5 rounded bg-steel border border-line text-txt-3 font-semibold">{lang.code}</span>
                          <span>{lang.label}</span>
                        </span>
                        {voice.langMode === lang.id && <Icon name="check" size={12} className="text-hi" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <textarea
                ref={textareaRef}
                className="flex-1 bg-transparent text-xs text-txt placeholder:text-txt-3 focus:outline-none resize-none px-2 py-1 leading-relaxed max-h-[120px]"
                style={{ minHeight: '38px' }}
                placeholder={
                  voice.isListening
                    ? 'جارٍ الاستماع... اضغط زر الميكروفون للإنهاء'
                    : voice.isTranscribing
                    ? 'تفريغ عبر Whisper AI...'
                    : 'اكتب سؤالك أو تحدث بالصوت… (عربي / English / لهجات)'
                }
                value={voice.interimTranscript ? (draft ? `${draft} ${voice.interimTranscript}` : voice.interimTranscript) : draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={busy}
                rows={1}
              />
              <button
                type="button"
                onClick={() => send()}
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-all ${
                  draft.trim() && !busy && !voice.isTranscribing
                    ? 'bg-hi text-white hover:bg-hi2 active:scale-95 shadow-sm'
                    : 'bg-steel-3 text-txt-3 opacity-60 cursor-not-allowed'
                }`}
                disabled={busy || !draft.trim() || voice.isTranscribing}
                aria-label="إرسال"
              >
                <Icon name="send" size={14} />
              </button>
            </div>
          </div>
        </section>
      )}
    </>
  )
}
