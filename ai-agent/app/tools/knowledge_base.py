"""
Domain HSE Knowledge Base & RAG Index for Elsewedy Cables (ESCA).

Provides high-accuracy domain knowledge retrieval for:
- ISO 45001:2018 Management System clauses & requirements
- OSHA 1910 General Industry & OSHA 1926 Construction Safety Regulations
- Elsewedy Cables (ESCA) 10 Safety Golden Rules & Plant SOPs
- Hazardous Materials / GHS Classifications & Gas Testing Limits
- Safety Metrics & Calculation Formulas (TRIR, LTIFR, Severity Rate, Days Until Stockout)
- SIMOPS (Simultaneous Operations) Rules & Conflict Matrices
"""
from typing import Optional


HSE_KNOWLEDGE_BASE: list[dict] = [
    # ── ISO 45001:2018 Management System ──────────────────────────────────────
    {
        "id": "ISO-45001-4",
        "category": "ISO_45001",
        "standard": "ISO 45001:2018",
        "clause": "Clause 4: Context of the Organization",
        "title_ar": "سياق المنظمة وتحديد نطاق نظام إدارة السلامة والصحة المهنية",
        "title_en": "Context of the Organization & Scope of OH&S Management System",
        "keywords": ["context", "scope", "stakeholders", "سياق", "أطراف معنية", "نطاق", "بيئة العمل"],
        "content_ar": (
            "المواصفة ISO 45001:2018 - البند 4: يتطلب من مصانع السويدي للكابلات فهم السياق الداخلي والخارجي، "
            "وتحديد احتياجات وتوقعات العمال والأطراف المعنية الأخرى، وتحديد النطاق الجغرافي والتشغيلي لنظام إدارة السلامة."
        ),
        "content_en": (
            "ISO 45001 Clause 4 requires establishing internal and external context, identifying worker "
            "and stakeholder expectations, and defining the operational boundaries of the OH&S management system."
        ),
    },
    {
        "id": "ISO-45001-5",
        "category": "ISO_45001",
        "standard": "ISO 45001:2018",
        "clause": "Clause 5: Leadership & Worker Participation",
        "title_ar": "القيادة ومشاركة العاملين في السلامة والصحة المهنية",
        "title_en": "Leadership, Commitment & Worker Participation",
        "keywords": ["leadership", "commitment", "participation", "consultation", "policy", "قيادة", "مشاركة العمال", "سياسة السلامة"],
        "content_ar": (
            "المواصفة ISO 45001:2018 - البند 5: تلزم الإدارة العليا في السويدي بتحمل المسؤولية الكاملة عن الوقاية من إصابات العمل، "
            "وإنشاء سياسة سلامة وصحة مهنية معتمدة، وضمان آليات واضحة للتشاور مع العمال ومشاركتهم الفعالة في تقييم المخاطر ولجان السلامة."
        ),
        "content_en": (
            "ISO 45001 Clause 5 mandates top management accountability, establishing a proactive OH&S policy, "
            "and ensuring active worker consultation and participation in safety committees and hazard identification."
        ),
    },
    {
        "id": "ISO-45001-6",
        "category": "ISO_45001",
        "standard": "ISO 45001:2018",
        "clause": "Clause 6: Planning & Hazard Identification (HIRA)",
        "title_ar": "التخطيط وتحديد المخاطر وتقييمها (HIRA) وتحديد الفرص والامتثال القانوني",
        "title_en": "Planning, Hazard Identification & Risk Assessment (HIRA)",
        "keywords": ["planning", "hira", "hazard", "risk assessment", "legal", "تخطيط", "تقييم المخاطر", "مصفوفة المخاطر", "سجل المخاطر"],
        "content_ar": (
            "المواصفة ISO 45001:2018 - البند 6: يشترط تنفيذ منهجية مستمرة لتحديد المخاطر وتقييم مخاطر الصحة والسلامة (HIRA)، "
            "وتطبيق تسلسل هرمي للضوابط (Hierarchy of Controls: الإزالة، الاستبدال، الضوابط الهندسية، الضوابط الإدارية، مهمات الوقاية الشخصية PPE)، "
            "وتحديد المتطلبات القانونية المصرية والامتثال لقانون العمل رقم 12 لسنة 2003 وقرارات السلامة المهنية."
        ),
        "content_en": (
            "ISO 45001 Clause 6 requires systematic Hazard Identification and Risk Assessment (HIRA), applying the Hierarchy "
            "of Controls (Elimination, Substitution, Engineering, Administrative, PPE), and maintaining legal compliance registers."
        ),
    },
    {
        "id": "ISO-45001-7",
        "category": "ISO_45001",
        "standard": "ISO 45001:2018",
        "clause": "Clause 7: Support, Competence & Training",
        "title_ar": "الدعم والكفاءة والتدريب والتوعية والمعلومات الموثقة",
        "title_en": "Support, Competence, Training, Awareness & Documented Information",
        "keywords": ["training", "competence", "awareness", "resources", "تدريب", "كفاءة", "شهادات", "توعية"],
        "content_ar": (
            "المواصفة ISO 45001:2018 - البند 7: يحدد متطلبات تحديد كفاءة العاملين وتوفير التدريب التخصصي اللازم (الأماكن المغلقة، العمل على ارتفاعات، الإسعافات الأولية، مكافحة الحريق)، "
            "وضمان تجديد الشهادات قبل انتهائها ومراقبة صلاحية تراخيص مزاولة المهن الخطرة."
        ),
        "content_en": (
            "ISO 45001 Clause 7 governs resource allocation, mandatory competency training, safety certificate validity tracking, "
            "and communication protocols."
        ),
    },
    {
        "id": "ISO-45001-8",
        "category": "ISO_45001",
        "standard": "ISO 45001:2018",
        "clause": "Clause 8: Operational Planning & Control (PTW & Emergency)",
        "title_ar": "التخطيط والضبط التشغيلي وتصاريح العمل والاستعداد للطوارئ",
        "title_en": "Operational Planning & Control, Permit to Work & Emergency Response",
        "keywords": ["operation", "ptw", "permit", "emergency", "contractors", "تشغيل", "تصريح عمل", "طوارئ", "مقاولين"],
        "content_ar": (
            "المواصفة ISO 45001:2018 - البند 8: يتطلب إدارة العمليات التشغيلية عبر نظام تصاريح العمل الإلكتروني (ePTW)، "
            "وإدارة المقاولين والموردين، والاستعداد والاستجابة لحالات الطوارئ وخطط الإخلاء وتجارب الطوارئ الدورية (Drills)."
        ),
        "content_en": (
            "ISO 45001 Clause 8 dictates operational controls including electronic Permit to Work (ePTW), contractor safety management, "
            "change management (MOC), and emergency response preparedness."
        ),
    },
    {
        "id": "ISO-45001-9",
        "category": "ISO_45001",
        "standard": "ISO 45001:2018",
        "clause": "Clause 9: Performance Evaluation & Internal Audit",
        "title_ar": "تقييم الأداء والتدقيق الداخلي ومراجعة الإدارة",
        "title_en": "Performance Evaluation, Monitoring, Internal Audit & Management Review",
        "keywords": ["evaluation", "audit", "monitoring", "kpi", "trir", "تدقيق", "مراجعة الإدارة", "مؤشرات أداء"],
        "content_ar": (
            "المواصفة ISO 45001:2018 - البند 9: يلزم مصانع السويدي برصد وقياس أداء السلامة عبر مؤشرات قياسية رائدة وتابعة (Leading & Lagging KPIs مثل TRIR و LTIFR)، "
            "وتنفيذ برنامج تدقيق داخلي مجدول ومراجعة دورية للإدارة العليا لتقييم ملاءمة وفعالية النظام."
        ),
        "content_en": (
            "ISO 45001 Clause 9 covers OH&S performance monitoring, Leading/Lagging indicators (TRIR, LTIFR), scheduled internal audits, "
            "and management review meetings."
        ),
    },
    {
        "id": "ISO-45001-10",
        "category": "ISO_45001",
        "standard": "ISO 45001:2018",
        "clause": "Clause 10: Incident Investigation, Nonconformity & CAPA",
        "title_ar": "التحقيق في الحوادث وحالات عدم المطابقة والإجراءات التصحيحية والتحسين المستمر",
        "title_en": "Incident Investigation, Nonconformity, CAPA & Continual Improvement",
        "keywords": ["incident", "investigation", "rca", "capa", "nonconformity", "تحقيق", "حوادث", "إجراء تصحيحي", "عدم مطابقة"],
        "content_ar": (
            "المواصفة ISO 45001:2018 - البند 10: يحدد بروتوكول الإبلاغ الفوري عن الحوادث وأشباه الحوادث (Near Misses)، "
            "وإجراء تحليل السبب الجذري (RCA عبر 5 Whys أو Fishbone Diagram)، وفتح إجراءات تصحيحية ووقائية (CAPA) محددة بوقت ومسؤولية ومتابعة فعاليتها."
        ),
        "content_en": (
            "ISO 45001 Clause 10 requires immediate incident/near-miss reporting, Root Cause Analysis (RCA), CAPA assignment with SLA tracking, "
            "and verification of corrective action effectiveness."
        ),
    },

    # ── OSHA Standards & Safety Regulations ──────────────────────────────────
    {
        "id": "OSHA-1910-1200",
        "category": "OSHA",
        "standard": "OSHA 29 CFR 1910.1200",
        "clause": "Hazard Communication & GHS",
        "title_ar": "معيار الإبلاغ عن المواد الكيميائية الخطرة ونظام GHS وصحائف SDS",
        "title_en": "Hazard Communication Standard (HazCom), GHS & Safety Data Sheets",
        "keywords": ["chemical", "ghs", "sds", "msds", "hazmat", "cas", "مواد كيميائية", "صحائف بيانات السلامة", "ملصقات تحذيرية"],
        "content_ar": (
            "معيار OSHA 1910.1200: يلزم المصنع بالحفاظ على سجل كامل للمواد الكيميائية مع أرقام CAS، "
            "وتوفير صحائف بيانات السلامة (SDS المكونة من 16 قسماً) باللغتين العربية والإنجليزية بالقرب من مواقع التخزين والاستخدام، "
            "ووضع ملصقات تحذيرية GHS كاملة (بيانات الخطر، رموز التحذير، إرشادات الوقاية)."
        ),
        "content_en": (
            "OSHA 1910.1200 mandates maintaining chemical inventories with CAS numbers, 16-section Safety Data Sheets (SDS) in accessible locations, "
            "and proper GHS pictograms, signal words, and hazard statements on all containers."
        ),
    },
    {
        "id": "OSHA-1910-146",
        "category": "OSHA",
        "standard": "OSHA 29 CFR 1910.146",
        "clause": "Permit-Required Confined Spaces (PRCS)",
        "title_ar": "معيار العمل داخل الأماكن المغلقة وتصاريح الدخول وفحص الغازات",
        "title_en": "Permit-Required Confined Spaces & Atmospheric Testing",
        "keywords": ["confined space", "gas test", "lel", "oxygen", "h2s", "co", "أماكن مغلقة", "فحص غازات", "أكسجين", "تصريح مكان مغلق"],
        "content_ar": (
            "معيار OSHA 1910.146: يحدد اشتراطات الدخول للأماكن المغلقة (الخزانات، غرف التفتيش، الأنفاق، الصوامع): "
            "1. استخراج تصريح دخول معتمد (Confined Space PTW). "
            "2. إجراء فحص غازات مستمر: الأكسجين O2 (19.5% إلى 23.5%)، الغازات القابلة للاشتعال LEL (< 10%)، أول أكسيد الكربون CO (< 35 ppm)، كبريتيد الهيدروجين H2S (< 10 ppm). "
            "3. توفير مراقب دخول خارجي (Standby Attendant) ووسائل إنقاذ دون دخول (Tripod & Harness)."
        ),
        "content_en": (
            "OSHA 1910.146 establishes PRCS entry protocols: atmospheric testing (O2: 19.5-23.5%, LEL: <10%, H2S: <10ppm, CO: <35ppm), "
            "dedicated Standby Attendant, mechanical ventilation, and non-entry rescue retrieval equipment."
        ),
    },
    {
        "id": "OSHA-1910-147",
        "category": "OSHA",
        "standard": "OSHA 29 CFR 1910.147",
        "clause": "Lockout / Tagout (LOTO) - Hazardous Energy Control",
        "title_ar": "معيار عزل مصادر الطاقة الخطرة وتأمين المعدات (LOTO)",
        "title_en": "Control of Hazardous Energy (Lockout/Tagout - LOTO)",
        "keywords": ["loto", "lockout", "tagout", "isolation", "energy", "عزل الطاقة", "لوتو", "قفل", "بطاقة تحذيرية"],
        "content_ar": (
            "معيار OSHA 1910.147: يحدد الخطوات الست لعزل الطاقة (الكهربائية، الميكانيكية، الهيدروليكية، الهوائية، الحرارية): "
            "1. الإخطار والتجهيز للإغلاق. 2. إيقاف المعدة. 3. عزل جميع مصادر الطاقة. 4. وضع الأقفال والبطاقات (LOTO Padlocks & Tags). "
            "5. تفريغ وتشتيت الطاقة المخزونة (Zero Energy State). 6. التحقق من العزل (Try-Step قبل بدء العمل)."
        ),
        "content_en": (
            "OSHA 1910.147 establishes the 6-step LOTO procedure: Preparation, Shutdown, Isolation, Lockout/Tagout application, "
            "Stored energy dissipation (Zero Energy Verification), and Isolation test."
        ),
    },
    {
        "id": "OSHA-1910-157",
        "category": "OSHA",
        "standard": "OSHA 29 CFR 1910.157",
        "clause": "Portable Fire Extinguishers & Inspection Cycles",
        "title_ar": "معيار مطافئ الحريق اليدوية ودورات الفحص والصيانة والاختبار الهيدروستاتيكي",
        "title_en": "Portable Fire Extinguishers: Inspection, Maintenance & Hydrostatic Testing",
        "keywords": ["fire", "extinguisher", "inspection", "hydrostatic", "طفاية حريق", "مطافئ", "فحص دوري", "اختبار هيدروستاتيكي"],
        "content_ar": (
            "معيار OSHA 1910.157 و NFPA 10: "
            "- الفحص البصري الدوري: شهرياً (التأكد من الوجود، سلامة مسمار الأمان، عداد الضغط في النطاق الأخضر، عدم وجود انسداد في الخرطوم، سلامة الهيكل). "
            "- الصيانة الشاملة: سنوياً بواسطة جهة معتمدة. "
            "- الاختبار الهيدروستاتيكي: كل 5 سنوات لمطافئ ثاني أكسيد الكربون CO2 ومطافئ الماء، وكل 12 سنة لمطافئ البودرة الكيميائية الجافة (DCP)."
        ),
        "content_en": (
            "OSHA 1910.157 & NFPA 10: Monthly visual inspections (pressure gauge, pin, seal, nozzle, unobstructed access), "
            "Annual maintenance check by certified technician, Hydrostatic testing every 5 years (CO2/Water) or 12 years (DCP dry chemical)."
        ),
    },
    {
        "id": "OSHA-1910-132",
        "category": "OSHA",
        "standard": "OSHA 29 CFR 1910.132",
        "clause": "Personal Protective Equipment (PPE) General Requirements",
        "title_ar": "معيار مهمات الوقاية الشخصية واختيارها وتقييم الحاجة ومطابقة المواصفات",
        "title_en": "Personal Protective Equipment (PPE) Assessment, Selection & Maintenance",
        "keywords": ["ppe", "helmet", "safety shoes", "gloves", "goggles", "مهمات وقاية", "خوذة", "حذاء سلامة", "قفازات", "نظارات"],
        "content_ar": (
            "معيار OSHA 1910.132 إلى 138: إلزام أصحاب الأعمال بتقييم مخاطر بيئة العمل واختيار مهمات الوقاية المعتمدة "
            "(خوذة رأس ANSI Z89.1، حذاء سلامة بنعل فولاذي ASTM F2413، نظارات واقية ANSI Z87.1، قفازات مقاومة للمواد الكيميائية أو القطع EN 388)، "
            "وتدريب العمال على استخدامها وصيانتها واستبدال التالف منها فوراً."
        ),
        "content_en": (
            "OSHA 1910.132 requires workplace PPE hazard assessment, certified equipment selection (ANSI/ASTM/EN standards), "
            "worker training on proper fit and maintenance, and immediate replacement upon wear or damage."
        ),
    },
    {
        "id": "OSHA-1926-501",
        "category": "OSHA",
        "standard": "OSHA 29 CFR 1926.501",
        "clause": "Fall Protection (Working at Heights)",
        "title_ar": "معيار الحماية من السقوط والعمل على ارتفاعات أعلى من 1.8 متر",
        "title_en": "Duty to Have Fall Protection (Working at Height > 1.8m)",
        "keywords": ["fall protection", "height", "harness", "lanyard", "scaffold", "سقوط", "ارتفاعات", "حزام أمان", "سقالة"],
        "content_ar": (
            "معيار OSHA 1926.501: يلزم بتوفير أنظمة حماية من السقوط عند العمل على ارتفاع 1.8 متر (6 أقدام) فأكثر: "
            "1. درابزينات حماية قياسية (Guardrails: علوي 42 بوصة، أوسط 21 بوصة، حاجز قدم Toeboard). "
            "2. نظام منع السقوط الفردي (Full Body Harness مع Shock-Absorbing Lanyard ونقطة تثبيت تتحمل 5000 رطل). "
            "3. فحص وتفتيش السقالات يومياً وتثبيت كارت الصلاحية الأخضر قبل الاستخدام."
        ),
        "content_en": (
            "OSHA 1926.501 mandates fall protection for heights exceeding 1.8m (6ft): Guardrail systems (42in top rail, 21in mid rail, toeboards), "
            "Personal Fall Arrest Systems (PFAS with 5,000 lbs anchorage point), and certified daily scaffold inspections with green tagging."
        ),
    },

    # ── Elsewedy Cables (ESCA) 10 Safety Golden Rules ──────────────────────
    {
        "id": "ESCA-GR-01",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #1",
        "clause": "Permit to Work (ePTW) Compliance",
        "title_ar": "القاعدة الذهبية 1: الالتزام الصارم بتصاريح العمل الإلكترونية ePTW",
        "title_en": "Golden Rule 1: Strict Compliance with Electronic Permit to Work (ePTW)",
        "keywords": ["golden rule", "ptw", "permit", "قواعد ذهبية", "تصريح عمل"],
        "content_ar": (
            "القاعدة الذهبية رقم 1 في مصانع السويدي للكابلات: يُمنع منعاً باتاً تنفيذ أي عمل حرج (أعمال ساخنة، أماكن مغلقة، "
            "عمل على ارتفاعات، حفر، أعمال كهربائية) دون استخراج تصريح عمل إلكتروني معتمد وموقّع من مسؤول السلامة ومسؤول المنطقة."
        ),
        "content_en": (
            "ESCA Golden Rule 1: No critical work (Hot Work, Confined Space, Working at Height, Excavation, Electrical) "
            "shall commence without an active, validated, and signed electronic Permit to Work (ePTW)."
        ),
    },
    {
        "id": "ESCA-GR-02",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #2",
        "clause": "Energy Isolation & Lockout / Tagout (LOTO)",
        "title_ar": "القاعدة الذهبية 2: عزل مصادر الطاقة وتطبيق نظام القفل والبطاقة LOTO",
        "title_en": "Golden Rule 2: Energy Isolation & Lockout / Tagout (LOTO)",
        "keywords": ["golden rule", "loto", "isolation", "قواعد ذهبية", "عزل طاقة"],
        "content_ar": (
            "القاعدة الذهبية رقم 2: يجب عزل واختبار وتفريغ جميع مصادر الطاقة الخطرة وتثبيت أقفال وبطاقات LOTO الشخصية "
            "قبل الدخول في أي أعمال صيانة أو تنظيف أو إصلاح للآلات والمعدات."
        ),
        "content_en": (
            "ESCA Golden Rule 2: All energy sources must be isolated, locked, tagged, and verified zero-energy state before any maintenance."
        ),
    },
    {
        "id": "ESCA-GR-03",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #3",
        "clause": "Working at Height & Fall Arrest",
        "title_ar": "القاعدة الذهبية 3: العمل على ارتفاعات واستخدام حزام الأمان الكامل",
        "title_en": "Golden Rule 3: Working at Height & Full Body Harness Usage",
        "keywords": ["golden rule", "height", "fall", "harness", "قواعد ذهبية", "عمل على ارتفاعات"],
        "content_ar": (
            "القاعدة الذهبية رقم 3: ارتداء حزام الأمان لكامل الجسم وتثبيته في نقطة تثبيت معتمدة عند العمل على ارتفاع 1.8 متر فأكثر، "
            "مع حظر استخدام السقالات غير المعتمدة أو السلالم المتهالكة."
        ),
        "content_en": (
            "ESCA Golden Rule 3: 100% tie-off with full body harness at heights >1.8m, using only inspected and certified scaffolding."
        ),
    },
    {
        "id": "ESCA-GR-04",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #4",
        "clause": "Confined Space Entry & Gas Testing",
        "title_ar": "القاعدة الذهبية 4: دخول الأماكن المغلقة وفحص الغازات المستمر",
        "title_en": "Golden Rule 4: Confined Space Entry & Continuous Gas Testing",
        "keywords": ["golden rule", "confined space", "gas test", "قواعد ذهبية", "مكان مغلق"],
        "content_ar": (
            "القاعدة الذهبية رقم 4: لا دخول لأي مكان مغلق دون فحص مسبق ومستمر لنسبة الأكسجين والغازات السامة والقابلة للاشتعال، "
            "مع وجود مراقب طوارئ مخصص وتوفير تهوية ميكانيكية مستمرة."
        ),
        "content_en": (
            "ESCA Golden Rule 4: No confined space entry without continuous 4-gas testing, dedicated standby watcher, and active ventilation."
        ),
    },
    {
        "id": "ESCA-GR-05",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #5",
        "clause": "SIMOPS Spatial & Temporal Conflict Verification",
        "title_ar": "القاعدة الذهبية 5: التحقق من تعارض العمليات المتزامنة SIMOPS في نفس المنطقة",
        "title_en": "Golden Rule 5: Simultaneous Operations (SIMOPS) Conflict Check",
        "keywords": ["golden rule", "simops", "conflict", "قواعد ذهبية", "تعارض عمليات"],
        "content_ar": (
            "القاعدة الذهبية رقم 5: يُحظر نهائياً تنفيذ أعمال ساخنة بالتزامن مع التعامل مع مواد كيميائية قابلة للاشتعال أو دهانات "
            "أو أعمال اختبارات ضغط في نفس المنطقة الجغرافية دون تصريح وفصل مكاني/زمني معتمد."
        ),
        "content_en": (
            "ESCA Golden Rule 5: Hot work is strictly forbidden concurrently with flammable chemical handling or pressure testing in the same zone."
        ),
    },
    {
        "id": "ESCA-GR-06",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #6",
        "clause": "Machine Guarding & Safety Interlocks",
        "title_ar": "القاعدة الذهبية 6: حواجز حماية الماكينات وحظر إلغاء أنظمة الأمان التلقائية",
        "title_en": "Golden Rule 6: Machine Guarding & Zero Bypassing of Interlocks",
        "keywords": ["golden rule", "machine guard", "interlock", "e-stop", "حماية ماكينات", "مفتاح طوارئ"],
        "content_ar": (
            "القاعدة الذهبية رقم 6: يُحظر إزالة أو تجاوز حواجز حماية الماكينات أو مفاتيح الطوارئ (E-Stops) أو الحساسات الضوئية (Light Curtains) أثناء تشغيل خطوط الإنتاج وسحب الكابلات."
        ),
        "content_en": (
            "ESCA Golden Rule 6: Never bypass machine guards, emergency stop pull cords, or optical safety curtains during cable production."
        ),
    },
    {
        "id": "ESCA-GR-07",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #7",
        "clause": "Chemical Handling & SDS Compliance",
        "title_ar": "القاعدة الذهبية 7: تداول المواد الكيميائية والالتزام بصحائف SDS",
        "title_en": "Golden Rule 7: Chemical Storage & SDS Compliance",
        "keywords": ["golden rule", "chemical", "sds", "مواد كيميائية"],
        "content_ar": (
            "القاعدة الذهبية رقم 7: الالتزام بارتداء مهمات الوقاية المخصصة للمواد الكيميائية وتخزين المواد في أحواض احتواء ثانوي (Secondary Containment Bunds) وفصل المواد غير المتوافقة كيميائياً."
        ),
        "content_en": (
            "ESCA Golden Rule 7: Secondary containment required for all chemicals, proper segregation of incompatible classes, and PPE matching SDS."
        ),
    },
    {
        "id": "ESCA-GR-08",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #8",
        "clause": "100% Mandatory PPE in Production Areas",
        "title_ar": "القاعدة الذهبية 8: الالتزام الكامل بمهمات الوقاية الشخصية الأساسية والتخصصية",
        "title_en": "Golden Rule 8: 100% PPE Compliance in Plant Zones",
        "keywords": ["golden rule", "ppe", "خوذة", "حذاء سلامة", "مهمات وقاية"],
        "content_ar": (
            "القاعدة الذهبية رقم 8: ارتداء مهمات الوقاية الأساسية (خوذة السلامة، حذاء السلامة ذو النعل الفولاذي، النظارات الواقية، السترة العاكسة) إلزامي فور الدخول إلى عنابر الإنتاج والساحات."
        ),
        "content_en": (
            "ESCA Golden Rule 8: Hard hat, steel-toe boots, safety glasses, and high-visibility vest are mandatory across all factory floors."
        ),
    },
    {
        "id": "ESCA-GR-09",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #9",
        "clause": "Traffic Management & Pedestrian / Forklift Segregation",
        "title_ar": "القاعدة الذهبية 9: فصل مسارات المشاة عن حركة الرافعات الشوكية والمعدات",
        "title_en": "Golden Rule 9: Pedestrian & Forklift Segregation / Speed Limits",
        "keywords": ["golden rule", "forklift", "traffic", "pedestrian", "رافعة شوكية", "مسار مشاة"],
        "content_ar": (
            "القاعدة الذهبية رقم 9: الالتزام بالسير في ممرات المشاة المحددة باللون الأصفر والأخضر، والالتزام بالسرعة القصوى للرافعات الشوكية (10 كم/ساعة)، وعدم ركوب أي شخص غير مخصص على المعدات."
        ),
        "content_en": (
            "ESCA Golden Rule 9: Pedestrians must use marked walkways; forklifts strictly limited to 10 km/h with 3-meter safety clearance."
        ),
    },
    {
        "id": "ESCA-GR-10",
        "category": "ESCA_GOLDEN_RULES",
        "standard": "ESCA Golden Safety Rule #10",
        "clause": "Immediate Incident & Near-Miss Reporting (Stop Work Authority)",
        "title_ar": "القاعدة الذهبية 10: الإبلاغ الفوري عن الحوادث وحق إيقاف العمل غير الآمن (SWA)",
        "title_en": "Golden Rule 10: Immediate Incident/Near-Miss Reporting & Stop Work Authority",
        "keywords": ["golden rule", "stop work", "reporting", "near miss", "إيقاف العمل", "إبلاغ فوري", "بلاغ"],
        "content_ar": (
            "القاعدة الذهبية رقم 10: يحق لجميع العاملين والمهندسين إيقاف أي عمل غير آمن فوراً (Stop Work Authority) دون أي مساءلة، "
            "مع الإبلاغ الفوري عن أي حادث أو شبه حادث أو تصرف غير آمن خلال 15 دقيقة عبر النظام."
        ),
        "content_en": (
            "ESCA Golden Rule 10: Every employee holds unconditional Stop Work Authority (SWA) for unsafe acts/conditions, with mandatory immediate reporting."
        ),
    },

    # ── Standard Safety Metric Calculations & Formulas ──────────────────────
    {
        "id": "HSE-METRIC-TRIR",
        "category": "CALCULATIONS",
        "standard": "OSHA / ISO HSE Metrics",
        "clause": "Total Recordable Incident Rate (TRIR)",
        "title_ar": "معادلة احتساب معدل الحوادث المسجلة الإجمالي (TRIR)",
        "title_en": "Total Recordable Incident Rate (TRIR) Formula & Definition",
        "keywords": ["trir", "rate", "formula", "calculation", "مؤشر trir", "معادلة", "حساب"],
        "content_ar": (
            "معادلة TRIR القياسية المعتمدة من OSHA: "
            "TRIR = (إجمالي الحوادث المسجلة Recordable Incidents × 200,000) ÷ إجمالي ساعات العمل الفعلية (Hours Worked). "
            "- المعامل 200,000 يمثل ساعات عمل 100 موظف بدوام كامل لمدة عام (100 موظف × 40 ساعة/أسبوع × 50 أسبوع). "
            "- الهدف المؤسسي في السويدي للكابلات: TRIR < 0.50."
        ),
        "content_en": (
            "TRIR Formula = (Total Recordable Incidents * 200,000) / Total Hours Worked. "
            "The 200,000 factor standardizes data to 100 full-time equivalent workers over one year. ESCA Target: TRIR < 0.50."
        ),
    },
    {
        "id": "HSE-METRIC-LTIFR",
        "category": "CALCULATIONS",
        "standard": "OSHA / ISO HSE Metrics",
        "clause": "Lost Time Injury Frequency Rate (LTIFR)",
        "title_ar": "معادلة احتساب معدل تكرار إصابات الوقت الضائع (LTIFR)",
        "title_en": "Lost Time Injury Frequency Rate (LTIFR) Formula & Definition",
        "keywords": ["ltifr", "lost time", "lti", "formula", "مؤشر ltifr", "وقت ضائع", "إصابات"],
        "content_ar": (
            "معادلة LTIFR القياسية: "
            "LTIFR = (إجمالي إصابات الوقت الضائع Lost Time Injuries × 1,000,000) ÷ إجمالي ساعات العمل الفعلية (Hours Worked). "
            "- المعامل 1,000,000 هو المعيار الدولي المعتمد في المنشآت الصناعية الكبرى لحساب معدل التكرار لكل مليون ساعة عمل. "
            "- الهدف المؤسسي في السويدي للكابلات: LTIFR = 0.00 (Zero LTI Policy)."
        ),
        "content_en": (
            "LTIFR Formula = (Number of Lost Time Injuries * 1,000,000) / Total Hours Worked. "
            "ESCA Target: LTIFR = 0.00 (Zero Lost Time Injury culture)."
        ),
    },
    {
        "id": "HSE-METRIC-DAYS-STOCKOUT",
        "category": "CALCULATIONS",
        "standard": "PPE Inventory Management",
        "clause": "Days Until Stockout Calculation",
        "title_ar": "معادلة احتساب الأيام المتبقية لنفاد مخزون مهمات الوقاية (Days Until Stockout)",
        "title_en": "Days Until Stockout Calculation for PPE Inventory",
        "keywords": ["stockout", "ppe inventory", "consumption", "balance", "أيام نفاد المخزون", "استهلاك المهمات"],
        "content_ar": (
            "معادلة الأيام المتبقية لنفاد المخزون: "
            "معدل الاستهلاك اليومي = الاستهلاك الشهري (Monthly Consumption) ÷ 30 يوماً. "
            "الأيام المتبقية حتى نفاد المخزون = الرصيد الحالي (Balance Qty) ÷ معدل الاستهلاك اليومي. "
            "- إذا كان الرصيد < حد إعادة الطلب (Reorder Threshold)، يتم إصدار تنبيه أحمر عاجل للتوريد."
        ),
        "content_en": (
            "Daily Consumption Rate = Monthly Consumption / 30.0. "
            "Days Until Stockout = Balance Quantity / Daily Consumption Rate. Trigger alert if Balance < Reorder Threshold."
        ),
    },
]


def search_hse_knowledge(query: str, category: Optional[str] = None, limit: int = 5) -> dict:
    """
    Retrieves the most relevant HSE knowledge documents, clauses, standards, and formulas.
    Uses multi-token keyword overlap scoring across Arabic & English text.
    """
    if not query or not query.strip():
        return {
            "total_matches": len(HSE_KNOWLEDGE_BASE),
            "results": HSE_KNOWLEDGE_BASE[:limit]
        }

    q_tokens = set(query.lower().replace("-", " ").replace(":", " ").split())
    stop_words = {"what", "is", "the", "and", "or", "for", "in", "to", "of", "a", "an", "ما", "هو", "هي", "في", "عن", "على", "من", "إلى", "مع"}
    q_tokens = {t for t in q_tokens if len(t) > 1 and t not in stop_words}

    scored_results = []
    for item in HSE_KNOWLEDGE_BASE:
        if category and item.get("category", "").upper() != category.upper().strip():
            continue

        score = 0
        searchable_text = (
            f"{item.get('standard', '')} {item.get('clause', '')} {item.get('title_ar', '')} "
            f"{item.get('title_en', '')} {item.get('content_ar', '')} {item.get('content_en', '')} "
            f"{' '.join(item.get('keywords', []))}"
        ).lower()

        for token in q_tokens:
            if token in searchable_text:
                score += 3
            if any(token in kw for kw in item.get("keywords", [])):
                score += 5
            if token in item.get("id", "").lower() or token in item.get("standard", "").lower():
                score += 8

        if score > 0:
            scored_results.append((score, item))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    matches = [item for score, item in scored_results[:limit]]

    if not matches:
        matches = [item for item in HSE_KNOWLEDGE_BASE if not category or item.get("category") == category][:limit]

    return {
        "query": query,
        "category_filter": category,
        "total_matches": len(matches),
        "results": matches
    }
