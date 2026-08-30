"""
ESCA HSE AI Agent - Safety Equipment, PPE, Fixed Emergency Assets & Firefighting Catalog

Massive multilingual registry covering 100+ industrial safety items, model numbers,
PPE classifications, fixed emergency assets, fire extinguishing gear, and common typos.
"""

from typing import Optional, Dict, Any, List
from .normalization import normalize_text


EQUIPMENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ══════════════════════════════════════════════════════════════════════════
    # 1. PERSONAL PROTECTIVE EQUIPMENT (PPE)
    # ══════════════════════════════════════════════════════════════════════════

    "PPE-EY-01": {
        "ppe_item_id": 2,
        "item_code": "PPE-EY-01",
        "name_ar": "نظارة واقية",
        "name_en": "Safety Glasses",
        "category": "EYE",
        "keywords": [
            "safety glasses", "safety glassess", "glassess", "glasses", "glass", "goggles",
            "goggle", "safety goggles", "eyewear", "spectacles", "eye protection", "eye safety",
            "protective glasses", "clear glasses", "anti-fog glasses", "uv safety glasses",
            "نظارة واقية", "نظارة", "نظارات", "نظاره", "نظارات واقية", "نظارة سلامة", "نظارات سلامة",
            "واقي أعين", "واقي عين", "نظارات حماية", "نظارة حماية", "نضارة", "نضارات", "نضاره سلامة", "سيفتي جلاسز"
        ]
    },

    "PPE-HD-01": {
        "ppe_item_id": 1,
        "item_code": "PPE-HD-01",
        "name_ar": "خوذة أمان (Hard Hat)",
        "name_en": "Safety Helmet",
        "category": "HEAD",
        "keywords": [
            "safety helmet", "helmet", "hard hat", "hard-hat", "hardhat", "head protection",
            "safety hat", "hemet", "helmets", "hard hats", "industrial helmet", "bump cap",
            "خوذة أمان", "خوذة", "خوذه", "خوذ", "خوذات", "كاب سلامة", "واقي رأس", "خوذة سلامة",
            "خوذه امان", "خوذة بيضاء", "خوذة صفراء", "هارد هات", "سيفتي هلمت"
        ]
    },

    "PPE-SH-01": {
        "ppe_item_id": 3,
        "item_code": "PPE-SH-01",
        "name_ar": "حذاء أمان بمقدمة فولاذية",
        "name_en": "Steel-Toe Safety Shoes",
        "category": "FOOT",
        "keywords": [
            "safety shoes", "safety boots", "steel toe", "steel-toe boots", "safety shoe", "safety boot",
            "boots", "shoes", "footwear", "foot protection", "work boots", "shose", "safty shoes",
            "steel toe shoes", "composite toe shoes", "metatarsal boots", "industrial footwear",
            "حذاء أمان", "حذاء سلامة", "سيفتي شوز", "جزمة أمان", "بوت أمان", "أحذية سلامة", "احذية سلامة",
            "أحذية أمان", "حذاء واقي", "سيفتي بوت", "شوز سلامة", "حذاء بمقدمة فولاذية", "بوت سلامة", "جزم سلامة"
        ]
    },

    "PPE-GL-05": {
        "ppe_item_id": 4,
        "item_code": "PPE-GL-05",
        "name_ar": "قفاز مقاوم للقطع مستوى 5",
        "name_en": "Cut-Resistant Gloves Level 5",
        "category": "HAND",
        "keywords": [
            "cut resistant gloves", "cut-resistant gloves", "safety gloves", "gloves", "glove", "cut gloves",
            "kevlar gloves", "leather gloves", "hand gloves", "hand protection", "gloevs", "gloovs",
            "level 5 cut gloves", "anti-cut gloves", "mechanic gloves", "impact gloves",
            "قفاز مقاوم للقطع", "قفازات مقاومة للقطع", "قفازات سلامة", "قفازات أمان", "قفاز أمان",
            "قفازات", "قفاز", "جوانتي", "كوانتي", "قفازات جلد", "قفاز عمل", "جوانتيات سلامة", "كوانتيات", "قفاز كيفلار"
        ]
    },

    "PPE-EL-01": {
        "ppe_item_id": 9,
        "item_code": "PPE-EL-01",
        "name_ar": "قفاز عازل للكهرباء 1000V",
        "name_en": "Insulated Electrical Gloves 1000V",
        "category": "ELECTRICAL",
        "keywords": [
            "electrical gloves", "insulated gloves", "1000v gloves", "high voltage gloves", "dielectric gloves",
            "electrician gloves", "class 0 gloves", "class 1 gloves", "voltage rated gloves",
            "قفاز عازل", "قفازات عازلة", "قفاز كهرباء", "قفازات كهربائية", "قفاز 1000v", "قفازات جهد عالي",
            "قفازات ضغط عالي", "جوانتي كهرباء عازل", "قفازات مطاطية عازلة"
        ]
    },

    "PPE-ER-01": {
        "ppe_item_id": 5,
        "item_code": "PPE-ER-01",
        "name_ar": "واقي أذن وسدادات صوت",
        "name_en": "Ear Protection (Plugs & Muffs)",
        "category": "HEARING",
        "keywords": [
            "earplugs", "ear plugs", "earmuffs", "ear muffs", "ear protection", "hearing protection", "hearing safety",
            "noise reduction", "hearing defenders", "acoustic protection",
            "واقي أذن", "واقي اذن", "سدادات أذن", "سدادات اذن", "سماعات أذن", "سماعات حماية الأذن", "واقيات الأذن",
            "حماية السمع", "سدادة أذن", "واقيات سمعية", "سماعات ضوضاء"
        ]
    },

    "PPE-RP-01": {
        "ppe_item_id": 6,
        "item_code": "PPE-RP-01",
        "name_ar": "كمامة نصف وجه وفلتر غازات",
        "name_en": "Half-Face Mask Respirator & Fume Filter",
        "category": "RESPIRATORY",
        "keywords": [
            "respirator", "half-face mask", "half face mask", "dust mask", "gas mask", "n95 mask", "respiratory mask",
            "mask", "masks", "respiratory protection", "ffp2 mask", "ffp3 mask", "cartridge respirator", "particulate mask",
            "كمامة نصف وجه", "كمامة", "كمامه", "كمامات", "قناع تنفس", "ماسك تنفس", "جهاز تنفس", "كمامة غازات",
            "كمامة أتربة", "فلتر غازات", "ماسك n95", "كمامة كيميائية"
        ]
    },

    "PPE-FR-01": {
        "ppe_item_id": 7,
        "item_code": "PPE-FR-01",
        "name_ar": "أفرول مقاوم للحريق FR",
        "name_en": "Flame Retardant Coverall (FR)",
        "category": "BODY",
        "keywords": [
            "fr coverall", "flame retardant coverall", "fire resistant overall", "coverall", "overall", "overalls",
            "work suit", "fr suit", "nomex coverall", "fire retardant suit", "welding suit",
            "أفرول fr", "افرول fr", "أفرول مقاوم للحريق", "افرول مقاوم للهب", "بدلة عمل", "أفرول سلامة", "بدلة وقاية",
            "افرول لحام", "بدلة مقاومة للنار", "أفرول نومكس", "افرول قطن معالج"
        ]
    },

    "PPE-HR-01": {
        "ppe_item_id": 8,
        "item_code": "PPE-HR-01",
        "name_ar": "حزام أمان كامل للعمل على ارتفاعات",
        "name_en": "Full Body Fall Arrest Harness",
        "category": "FALL_PROTECTION",
        "keywords": [
            "harness", "full body harness", "safety harness", "safety belt", "fall arrest harness", "lanyard",
            "fall protection", "double lanyard", "shock absorbing lanyard", "scaffold harness", "safety rope",
            "حزام أمان كامل", "حزام أمان", "حزام امان", "حزام باراشوت", "حبل أمان", "حزام عمل على ارتفاعات",
            "حزام سقوط", "حزام سلامة كامل", "حبل امتصاص صدمات", "معدة عمل على ارتفاع"
        ]
    },

    "PPE-FS-01": {
        "ppe_item_id": 10,
        "item_code": "PPE-FS-01",
        "name_ar": "درع واقي للوجه",
        "name_en": "Clear Face Shield / Grinding Visor",
        "category": "FACE",
        "keywords": [
            "face shield", "faceshield", "face visor", "grinding shield", "welding shield", "face protection",
            "polycarbonate visor", "safety visor", "chemical splash shield",
            "درع وجه", "واقي وجه", "شيلد وجه", "قناع وجه شفاف", "درع حماية الوجه", "واقي الوجه للصاروخ", "شيلد حماية"
        ]
    },

    "GLV-CHEM-QA": {
        "ppe_item_id": 12,
        "item_code": "GLV-CHEM-QA",
        "name_ar": "قفازات مقاومة للمواد الكيميائية (نيتريل)",
        "name_en": "Chemical Resistant Nitrile Gloves",
        "category": "HAND",
        "keywords": [
            "chemical gloves", "chemical resistant gloves", "nitrile gloves", "acid gloves", "neoprene gloves",
            "heavy duty chemical gloves", "solvent resistant gloves",
            "قفازات كيميائية", "قفازات مواد كيميائية", "قفازات أحماض", "قفازات كيميكال", "قفازات نيتريل", "جوانتي كيميائي"
        ]
    },

    "PPE-ARC-01": {
        "ppe_item_id": 13,
        "item_code": "PPE-ARC-01",
        "name_ar": "بدلة ومهمات حماية القوس الكهربائي Arc Flash 40 cal",
        "name_en": "Arc Flash Protection Suit 40 cal/cm2",
        "category": "ELECTRICAL",
        "keywords": [
            "arc flash suit", "arc flash", "40 cal suit", "arc flash ppe", "arc flash hood", "cal/cm2",
            "بدلة قوس كهربائي", "بدلة ارك فلاش", "حماية القوس الكهربائي", "بدلة ضغط عالي 40 كالوري", "هود ارك فلاش"
        ]
    },

    "PPE-SCBA-01": {
        "ppe_item_id": 14,
        "item_code": "PPE-SCBA-01",
        "name_ar": "جهاز تنفس مستقل بالهواء المضغوط SCBA",
        "name_en": "Self-Contained Breathing Apparatus (SCBA)",
        "category": "RESPIRATORY",
        "keywords": [
            "scba", "breathing apparatus", "self contained breathing", "air pack", "confined space breathing",
            "جهاز تنفس مستقل", "اسطوانة تنفس", "جهاز scba", "تنفس صناعي للهواء المضغوط", "طقم تنفس اماكن مغلقة"
        ]
    },

    "PPE-VEST-01": {
        "ppe_item_id": 15,
        "item_code": "PPE-VEST-01",
        "name_ar": "سترة فوسفورية عاكسة للضوء (High-Vis Vest)",
        "name_en": "High-Visibility Safety Vest",
        "category": "BODY",
        "keywords": [
            "high vis vest", "hi vis vest", "reflective vest", "safety vest", "high-visibility jacket",
            "سترة عاكسة", "سترة فوسفورية", "سديري أمان", "سديري سلامة", "سترة سلامة عاكسة", "فيست أمان", "فيست سلامة"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 2. FIXED SAFETY ASSETS & EMERGENCY STATIONS
    # ══════════════════════════════════════════════════════════════════════════

    "ASSET-EYEWASH-01": {
        "asset_summary_id": 1,
        "asset_type": "EMERGENCY_SHOWER",
        "name_ar": "محطة غسيل عيون ودش طوارئ",
        "name_en": "Emergency Shower / Eyewash Station",
        "keywords": [
            "eyewash station", "emergency eyewash", "eyewash", "eye wash", "emergency shower", "safety shower",
            "drench shower", "combination shower eyewash", "deluge shower",
            "محطة غسيل عيون", "محطة غسيل العيون", "غسيل عيون", "دش طوارئ", "دش الطوارئ", "دش سلامة", "غسالة عيون",
            "دش وغسيل عيون", "محطة طوارئ كيميائية"
        ]
    },

    "ASSET-AED-01": {
        "asset_summary_id": 8,
        "asset_type": "AED",
        "name_ar": "جهاز الصدمات الكهربائية الآلي للقلب (AED)",
        "name_en": "Automated External Defibrillator (AED)",
        "keywords": [
            "aed", "defibrillator", "automated external defibrillator", "cpr aed", "cardiac defibrillator",
            "جهاز aed", "جهاز الصدمات", "جهاز الصدمات الكهربائية", "صدمات القلب", "مزيل الرجفان الآلي", "جهاز إنعاش القلب"
        ]
    },

    "ASSET-FIRSTAID-01": {
        "asset_summary_id": 8,
        "asset_type": "FIRST_AID_STATION",
        "name_ar": "صندوق ومحطة الإسعافات الأولية",
        "name_en": "First Aid Cabinet & Station",
        "keywords": [
            "first aid station", "first aid kit", "first aid box", "first aid", "emergency medical box",
            "صندوق إسعاف", "صندوق اسعاف", "محطة إسعاف أولي", "إسعافات أولية", "اسعافات اولية", "شنطة اسعافات", "صيدلية الإسعاف"
        ]
    },

    "ASSET-SPILLKIT-01": {
        "asset_summary_id": 6,
        "asset_type": "SPILL_KIT",
        "name_ar": "مجموعة التعامل مع انسكاب الكيماويات Spill Kit",
        "name_en": "Chemical Spill Response Kit",
        "keywords": [
            "spill kit", "chemical spill kit", "spill response", "oil spill kit", "absorbent pads",
            "سبيل كيت", "عدة انسكاب", "مجموعة انسكاب كيميائي", "طقم طوارئ انسكاب", "ممتصات كيميائية", "طقم معالجة التسريب"
        ]
    },

    "ASSET-FIREPANEL-01": {
        "asset_summary_id": 5,
        "asset_type": "FIRE_ALARM_PANEL",
        "name_ar": "لوحة إنذار الحريق الرئيسية (FACP)",
        "name_en": "Fire Alarm Control Panel (FACP)",
        "keywords": [
            "fire alarm panel", "fire control panel", "alarm panel", "facp", "main fire alarm",
            "لوحة إنذار الحريق", "لوحة انذار الحريق", "لوحة الحريق", "لوحة الإنذار", "لوحة التحكم الرئيسية للحريق"
        ]
    },

    "ASSET-HYDRANT-01": {
        "asset_summary_id": 4,
        "asset_type": "FIRE_HYDRANT",
        "name_ar": "صندوق وحنفية إطفاء الحريق وبكرة الخراطيم",
        "name_en": "Fire Hydrant Cabinet & Hose Reel",
        "keywords": [
            "fire hydrant", "hydrant cabinet", "fire hose cabinet", "hose reel", "landing valve", "fire hose",
            "صندوق حريق", "صندوق إطفاء", "حنفية حريق", "خرطوم حريق", "بكرة خرطوم", "صمام الحريق", "كابينة إطفاء"
        ]
    },

    "ASSET-MCP-01": {
        "asset_summary_id": 7,
        "asset_type": "MANUAL_CALL_POINT",
        "name_ar": "كاسر زجاج الإنذار اليدوي (Manual Call Point)",
        "name_en": "Manual Call Point (MCP) / Break Glass",
        "keywords": [
            "manual call point", "break glass", "fire button", "alarm pull station", "mcp",
            "كاسر زجاج", "زر إنذار يدوي", "نقطة نداء يدوية", "كاسر إنذار الحريق", "سارينة يدوية"
        ]
    },

    "ASSET-SMOKE-01": {
        "asset_summary_id": 9,
        "asset_type": "SMOKE_DETECTOR",
        "name_ar": "كاشف الدخان البصري",
        "name_en": "Optical Smoke Detector",
        "keywords": [
            "smoke detector", "optical smoke detector", "smoke sensor", "fire detector",
            "كاشف دخان", "حساس دخان", "كواشف الدخان", "مستشعر دخان الحريق"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 3. FIRE EXTINGUISHERS & SUPPRESSION EQUIPMENT
    # ══════════════════════════════════════════════════════════════════════════

    "FE-CO2": {
        "equipment_id": 2,
        "subtype": "CO2",
        "name_ar": "طفاية ثاني أكسيد الكربون CO2",
        "name_en": "Carbon Dioxide (CO2) Fire Extinguisher",
        "keywords": [
            "co2 extinguisher", "co2 fire extinguisher", "co2", "carbon dioxide extinguisher",
            "co2 6kg", "co2 5kg", "co2 2kg",
            "طفاية co2", "طفاية ثاني أكسيد الكربون", "طفاية ثاني اكسيد الكربون", "طفاية غاز", "طفاية كهرباء", "طفاية كربون"
        ]
    },

    "FE-DCP": {
        "equipment_id": 1,
        "subtype": "DRY_POWDER",
        "name_ar": "طفاية بودرة كيميائية جافة (DCP/ABC)",
        "name_en": "Dry Chemical Powder (DCP/ABC) Extinguisher",
        "keywords": [
            "dry powder extinguisher", "dcp extinguisher", "dry chemical extinguisher", "powder extinguisher",
            "abc extinguisher", "dry powder 6kg", "dry powder 9kg", "dry powder 12kg", "bavaria dcp",
            "طفاية بودرة", "طفاية بودرة جافة", "طفاية dcp", "طفاية بافاريا", "طفاية abc", "طفاية حريق بودرة"
        ]
    },

    "FE-FOAM": {
        "equipment_id": 4,
        "subtype": "FOAM",
        "name_ar": "طفاية رغوة ميكانيكية AFFF Foam",
        "name_en": "Aqueous Film Forming Foam (AFFF) Extinguisher",
        "keywords": [
            "foam extinguisher", "foam fire extinguisher", "foam 9l", "afff extinguisher", "foam 50l",
            "طفاية رغوة", "طفاية فوم", "طفاية رغوية", "طفاية afff", "طفاية سوائل بترولية"
        ]
    },

    "FE-WATER": {
        "equipment_id": 5,
        "subtype": "WATER",
        "name_ar": "طفاية ماء مضغوط / رذاذ الماء",
        "name_en": "Water Mist / Pressurized Water Extinguisher",
        "keywords": [
            "water extinguisher", "water mist extinguisher", "pressurized water extinguisher", "water 9l",
            "طفاية ماء", "طفاية مياه", "طفاية رذاذ الماء", "طفاية ماء مضغوط"
        ]
    },

    "FE-WETCHEM": {
        "equipment_id": 6,
        "subtype": "WET_CHEMICAL",
        "name_ar": "طفاية كيماويات رطبة لزيوت الطعام (Class K/F)",
        "name_en": "Wet Chemical Class K/F Extinguisher",
        "keywords": [
            "wet chemical extinguisher", "class k extinguisher", "class f extinguisher", "kitchen fire extinguisher",
            "طفاية كيماويات رطبة", "طفاية كلاس k", "طفاية مطابخ", "طفاية زيوت وشحوم"
        ]
    },

    "FE-CLEAN": {
        "equipment_id": 7,
        "subtype": "CLEAN_AGENT",
        "name_ar": "طفاية غاز نظيف FM-200 / NOVEC",
        "name_en": "Clean Agent (FM-200 / NOVEC 1230 / FE-36) Extinguisher",
        "keywords": [
            "clean agent extinguisher", "fm200 extinguisher", "fm-200", "novec extinguisher", "novec 1230", "fe-36",
            "طفاية غاز نظيف", "طفاية fm200", "طفاية نوفيك", "طفاية غرف سيرفرات", "طفاية اجهزة الكترونية"
        ]
    },

    "FE-WHEELED-DCP": {
        "equipment_id": 8,
        "subtype": "WHEELED_POWDER",
        "name_ar": "طفاية بودرة مجرورة على عجلات 25/50 كجم",
        "name_en": "Wheeled Dry Chemical Extinguisher 25kg/50kg",
        "keywords": [
            "wheeled extinguisher", "wheeled dcp", "50kg powder extinguisher", "25kg dcp extinguisher", "mobile extinguisher",
            "طفاية مجرورة", "طفاية على عجل", "طفاية عجلات 50 كجم", "طفاية بودرة 25 كجم", "طفاية عربة"
        ]
    },
}


def extract_equipment_info(text: str) -> Optional[Dict[str, Any]]:
    """
    Parses and matches any equipment, PPE item, fire safety device, or fixed safety asset
    from user prompt in Arabic or English with typo and synonym tolerance.
    """
    if not text:
        return None
    clean = normalize_text(text).lower()
    padded = f" {clean} "

    # 1. Exact / Substring keyword match (Prioritize longest matched keywords)
    best_match = None
    max_len = 0

    for eq_code, info in EQUIPMENT_REGISTRY.items():
        for kw in info["keywords"]:
            norm_kw = normalize_text(kw).lower()
            if f" {norm_kw} " in padded or norm_kw in clean:
                if len(norm_kw) > max_len:
                    max_len = len(norm_kw)
                    best_match = {
                        "equipment_code": eq_code,
                        "item_code": info.get("item_code"),
                        "ppe_item_id": info.get("ppe_item_id"),
                        "equipment_id": info.get("equipment_id"),
                        "asset_summary_id": info.get("asset_summary_id"),
                        "name_ar": info.get("name_ar"),
                        "name_en": info.get("name_en"),
                        "category": info.get("category"),
                        "subtype": info.get("subtype"),
                        "matched_keyword": kw
                    }

    # 2. Fuzzy / Typo matching for common terms if no exact match
    if not best_match:
        typo_lookup = {
            ("glassess", "glasss", "gloasses", "gogles", "spectacels", "sunglasses", "glases"): "PPE-EY-01",
            ("hemet", "helment", "helmt", "hardhats", "hard-hats", "helmits"): "PPE-HD-01",
            ("gloevs", "gloovs", "glovese", "glovs", "glovez"): "PPE-GL-05",
            ("shose", "shoos", "bootes", "boote", "safty boot", "safty shoe"): "PPE-SH-01",
            ("eywash", "eyewashs", "showere", "eywash station"): "ASSET-EYEWASH-01",
            ("extingusher", "extinguisher", "extingish", "extingwisher"): "FE-DCP",
            ("defib", "defibrilator", "cpr machine"): "ASSET-AED-01",
        }
        for typo_keys, target_code in typo_lookup.items():
            if any(tk in clean for tk in typo_keys):
                info = EQUIPMENT_REGISTRY.get(target_code)
                if info:
                    best_match = {
                        "equipment_code": target_code,
                        "item_code": info.get("item_code"),
                        "ppe_item_id": info.get("ppe_item_id"),
                        "equipment_id": info.get("equipment_id"),
                        "asset_summary_id": info.get("asset_summary_id"),
                        "name_ar": info.get("name_ar"),
                        "name_en": info.get("name_en"),
                        "category": info.get("category"),
                        "subtype": info.get("subtype"),
                        "matched_keyword": target_code
                    }
                    break

    return best_match


def search_equipment_catalog(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Searches the equipment catalog by query keyword."""
    if not query:
        return []
    clean = normalize_text(query)
    results = []
    for code, info in EQUIPMENT_REGISTRY.items():
        score = 0
        if clean in normalize_text(code):
            score += 10
        if clean in normalize_text(info.get("name_en", "")):
            score += 8
        if clean in normalize_text(info.get("name_ar", "")):
            score += 8
        for kw in info.get("keywords", []):
            if clean in normalize_text(kw):
                score += 5
                break
        if score > 0:
            results.append({"code": code, "score": score, **info})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
