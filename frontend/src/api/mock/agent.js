import * as db from './data.js'

/**
 * Stand-in for the FastAPI Q&A endpoint (AI Student 2).
 *
 * The real service hands the question to an LLM with a fixed tool list and
 * lets it pick which tools to call. This mock keyword-routes to the *same*
 * tool names and returns the same envelope — so the chat panel is built
 * against the real response shape, and swapping in the live agent needs no
 * UI change. Read-only: it answers, it never acts.
 */

const TOOLS = {
  get_open_incidents() {
    const open = db.incidents.filter((i) => i.status !== 'مغلق')
    return {
      rows: open.map((i) => `${i.id} · ${i.zone} · ${i.severity} · ${i.status}`),
      text:
        `فيه ${open.length} بلاغات مفتوحة دلوقتي:\n` +
        open.map((i) => `• ${i.id} — ${i.description} (${i.zone}) · خطورة ${i.severity} · ${i.status}، مسؤول: ${i.owner}`).join('\n') +
        `\n\nأخطرها ${open.find((i) => i.severityTone === 'cr')?.id || '—'} لأنها مصنّفة خطورة عالية ولسه تحت التحقيق.`,
    }
  },

  get_expiring_training() {
    const expired = db.trainingExpiring.filter((t) => t.status === 'منتهية')
    const soon = db.trainingExpiring.filter((t) => t.status === 'قريباً')
    return {
      rows: db.trainingExpiring.map((t) => `${t.employee} · ${t.certificate} · ${t.expires}`),
      text:
        `${expired.length} شهادات منتهية فعلاً و${soon.length} هتنتهي خلال الشهر.\n\n` +
        `المنتهية (ممنوع دخولهم المناطق الحرجة لحد التجديد):\n` +
        expired.map((t) => `• ${t.employee} — ${t.certificate} — انتهت ${t.expires}`).join('\n') +
        `\n\nأقربهم في التجديد: ${soon[0]?.employee} — ${soon[0]?.certificate} يوم ${soon[0]?.expires}.`,
    }
  },

  get_permit_status() {
    const expiring = db.permits.filter((p) => p.statusTone === 'wn')
    const pending = db.permits.filter((p) => p.status === 'بانتظار الموافقة')
    const blocked = db.permits.filter((p) => p.statusTone === 'cr')
    return {
      rows: db.permits.map((p) => `${p.id} · ${p.zone} · ${p.status}`),
      text:
        `حالة التصاريح النهارده:\n` +
        `• ${expiring.length} تصاريح قرب ما تنتهي: ${expiring.map((p) => `${p.id} (لحد ${p.to})`).join('، ')}\n` +
        `• ${pending.length} بانتظار الموافقة\n` +
        `• ${blocked.length} موقوف أو مرفوض — ${blocked.map((p) => `${p.id}: ${p.status}`).join('، ')}\n\n` +
        `متوسط زمن دورة الاعتماد ${db.permitStats.avgApprovalMinutes} دقيقة.`,
    }
  },

  get_fire_equipment_due() {
    return {
      rows: db.fireAttention.map((f) => `${f.code} · ${f.location} · ${f.issue}`),
      text:
        `${db.fireAttention.length} طفايات محتاجة إجراء فوري:\n` +
        db.fireAttention.map((f) => `• ${f.code} — ${f.location} — ${f.issue}`).join('\n') +
        `\n\nالجاهزية العامة ${db.fireStats.readiness}% (${db.fireStats.serviceable} من ${db.fireStats.total}).`,
    }
  },

  get_zone_incident_ranking() {
    const counts = {}
    db.incidents.forEach((i) => {
      counts[i.zone] = (counts[i.zone] || 0) + 1
    })
    const ranked = Object.entries(counts).sort((a, b) => b[1] - a[1])
    return {
      rows: ranked.map(([z, n]) => `${z} · ${n}`),
      text:
        `ترتيب المناطق حسب عدد البلاغات المسجّلة:\n` +
        ranked.map(([z, n], idx) => `${idx + 1}. ${z} — ${n}`).join('\n') +
        `\n\n${ranked[0][0]} في المقدمة، ومؤشر السلامة بتاعها ${
          db.safetyByZone.find((s) => s.zone.includes(ranked[0][0].slice(0, 12)))?.score ?? '—'
        }% — يستاهل مراجعة JSA للمنطقة.`,
    }
  },

  get_overdue_capa() {
    const late = db.capa.filter((c) => c.status === 'متأخر')
    const running = db.capa.filter((c) => c.status === 'جاري')
    return {
      rows: db.capa.map((c) => `${c.id} · ${c.action} · ${c.status}`),
      text:
        `${late.length} إجراء تصحيحي متأخر عن موعده و${running.length} جاري التنفيذ.\n\n` +
        late.map((c) => `• ${c.id} — ${c.action} — كان مستحق ${c.due} (${c.owner})`).join('\n') +
        `\n\nنسبة الإغلاق في الموعد ${db.leadingIndicators[0].value}% والهدف ≥ 90%.`,
    }
  },

  get_kpis() {
    return {
      rows: db.reportKpis.map((k) => `${k.key} = ${k.value}`),
      text:
        `المؤشرات الرئيسية لسنة 2026:\n` +
        db.reportKpis.map((k) => `• ${k.key} = ${k.value} — ${k.label} (${k.target})`).join('\n') +
        `\n\nكل المؤشرات داخل الهدف، وTRIR نزل من ${db.trirTrend[0].trir} سنة 2022 لـ ${db.trirTrend.at(-1).trir} دلوقتي.`,
    }
  },

  get_high_risks() {
    const high = db.hazards.filter((h) => h.probability * h.severity >= 15)
    return {
      rows: high.map((h) => `${h.code} · ${h.hazard} · ${h.probability * h.severity}`),
      text:
        `${high.length} مخاطر بدرجة عالية أو أعلى (احتمالية × شدة ≥ 15):\n` +
        high.map((h) => `• ${h.code} — ${h.hazard} (${h.zone}) — درجة ${h.probability * h.severity}، متبقية ${h.residual}`).join('\n') +
        `\n\nالضوابط الحالية بتنزّل الدرجة المتبقية لمتوسط ${(high.reduce((a, h) => a + h.residual, 0) / high.length).toFixed(1)}.`,
    }
  },

  get_sensor_readings() {
    const s = db.sensorBaseline
    return {
      rows: s.map((x) => `${x.id} · ${x.value} ${x.unit}`),
      text:
        `آخر قراءات الحساسات:\n` +
        s.map((x) => `• ${x.name} — ${x.value} ${x.unit} (${x.limitLabel})`).join('\n') +
        `\n\nأكسجين خزان المياه الأرضي تحت الحد الآمن — التصريح PTW-2026-0409 اتوقف تلقائياً.`,
    }
  },
}

/** question keywords → tool. First match wins, same as a small router. */
const ROUTES = [
  [['حادث', 'حوادث', 'بلاغ', 'بلاغات', 'إصاب', 'مفتوح'], 'get_open_incidents'],
  [['تدريب', 'شهاد', 'دورة', 'تأهيل', 'كفاء'], 'get_expiring_training'],
  [['تصريح', 'تصاريح', 'permit', 'ptw'], 'get_permit_status'],
  [['طفاي', 'حريق', 'إطفاء'], 'get_fire_equipment_due'],
  [['منطقة', 'مناطق', 'قسم', 'أقسام', 'أعلى', 'ترتيب'], 'get_zone_incident_ranking'],
  [['capa', 'إجراء', 'إجراءات', 'تصحيح', 'متأخر'], 'get_overdue_capa'],
  [['مؤشر', 'trir', 'ltifr', 'kpi', 'أداء'], 'get_kpis'],
  [['مخاطر', 'خطر', 'hira', 'تقييم'], 'get_high_risks'],
  [['حساس', 'قراءة', 'قراءات', 'غاز', 'ضوضاء', 'أكسجين', 'iot'], 'get_sensor_readings'],
]

export function answer(question) {
  const q = (question || '').toLowerCase()

  const hit = ROUTES.find(([keys]) => keys.some((k) => q.includes(k)))
  if (!hit) {
    return {
      answer:
        'ممكن أجاوب على أي سؤال متعلق بالبيانات الحية في النظام: الحوادث والبلاغات، تصاريح العمل، ' +
        'الشهادات والتدريب، معدات الحريق، سجل المخاطر، الإجراءات التصحيحية، مؤشرات الأداء، وقراءات الحساسات.\n\n' +
        'جرّب مثلاً: «إيه الحوادث المفتوحة دلوقتي؟» أو «مين الموظفين اللي شهاداتهم منتهية؟».',
      tools: [],
      readOnly: true,
    }
  }

  const [, toolName] = hit
  const result = TOOLS[toolName]()
  return {
    answer: result.text,
    tools: [{ name: toolName, rowCount: result.rows.length, sample: result.rows.slice(0, 3) }],
    readOnly: true,
  }
}
