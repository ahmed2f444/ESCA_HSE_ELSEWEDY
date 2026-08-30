"""
ESCA HSE AI Agent - Hazardous Materials (HazMat), Chemicals & Industrial Gases Catalog

Comprehensive multilingual registry covering industrial chemicals, cable polymers,
solvents, compressed gases, GHS classifications, CAS numbers, and storage compatibility.
"""

from typing import Optional, Dict, Any, List
from .normalization import normalize_text


CHEMICAL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ══════════════════════════════════════════════════════════════════════════
    # 1. INDUSTRIAL ACIDS & BASES
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-H2SO4": {
        "chemical_id": 1,
        "trade_name": "Sulfuric Acid 98%",
        "chemical_name": "Sulfuric Acid",
        "formula": "H2SO4",
        "cas_number": "7664-93-9",
        "un_number": "UN1830",
        "ghs_classes": ["CORROSIVE", "ACUTE_TOXICITY"],
        "storage_class": "ACID_INORGANIC",
        "keywords": [
            "sulfuric acid", "sulphuric acid", "h2so4", "battery acid", "oil of vitriol",
            "حمض الكبريتيك", "حمض كبريتيك", "مية نار", "حمض الكبريت", "حمض السلفوريك"
        ]
    },

    "CHEM-HCL": {
        "chemical_id": 2,
        "trade_name": "Hydrochloric Acid 33%",
        "chemical_name": "Hydrochloric Acid / Muriatic Acid",
        "formula": "HCl",
        "cas_number": "7647-01-0",
        "un_number": "UN1789",
        "ghs_classes": ["CORROSIVE", "TOXIC_INHALATION"],
        "storage_class": "ACID_INORGANIC",
        "keywords": [
            "hydrochloric acid", "hcl", "muriatic acid", "hydrogen chloride aqueous",
            "حمض الهيدروكلوريك", "حمض هيدروكلوريك", "حمض كلور الماء", "حمض الكلور", "هيدروكلوريك"
        ]
    },

    "CHEM-NAOH": {
        "chemical_id": 3,
        "trade_name": "Caustic Soda Flakes 99%",
        "chemical_name": "Sodium Hydroxide",
        "formula": "NaOH",
        "cas_number": "1310-73-2",
        "un_number": "UN1823",
        "ghs_classes": ["CORROSIVE", "SKIN_CORROSION"],
        "storage_class": "BASE_INORGANIC",
        "keywords": [
            "sodium hydroxide", "caustic soda", "naoh", "lye", "soda lye", "caustic flakes",
            "هيدروكسيد الصوديوم", "الصودا الكاوية", "صودا كاوية", "بوتاس", "قشور الصودا"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 2. INDUSTRIAL SOLVENTS & DEGREASERS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-TOLUENE": {
        "chemical_id": 4,
        "trade_name": "Industrial Toluene",
        "chemical_name": "Methylbenzene / Toluene",
        "formula": "C7H8",
        "cas_number": "108-88-3",
        "un_number": "UN1294",
        "ghs_classes": ["FLAMMABLE_LIQUID", "REPRODUCTIVE_TOXICITY", "STOT_SE"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "toluene", "toluol", "methylbenzene", "thinner toluene",
            "تولوين", "مذيب تولوين", "ميثيل بنزين", "مذيب عضوي تولوين"
        ]
    },

    "CHEM-XYLENE": {
        "chemical_id": 5,
        "trade_name": "Mixed Xylene Solvent",
        "chemical_name": "Dimethylbenzene / Xylene",
        "formula": "C8H10",
        "cas_number": "1330-20-7",
        "un_number": "UN1307",
        "ghs_classes": ["FLAMMABLE_LIQUID", "ACUTE_TOXICITY", "SKIN_IRRITANT"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "xylene", "xylol", "mixed xylenes", "dimethylbenzene",
            "زايلين", "زايلول", "مذيب زايلين", "ثنائي ميثيل بنزين"
        ]
    },

    "CHEM-ACETONE": {
        "chemical_id": 6,
        "trade_name": "Pure Acetone Technical Grade",
        "chemical_name": "Propan-2-one / Acetone",
        "formula": "C3H6O",
        "cas_number": "67-64-1",
        "un_number": "UN1090",
        "ghs_classes": ["FLAMMABLE_LIQUID", "EYE_IRRITANT"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "acetone", "propanone", "dimethyl ketone", "cleaning solvent acetone",
            "اسيتون", "أسيتون", "مذيب اسيتون", "بروبانون"
        ]
    },

    "CHEM-MEK": {
        "chemical_id": 7,
        "trade_name": "Methyl Ethyl Ketone (MEK)",
        "chemical_name": "Butan-2-one / MEK",
        "formula": "C4H8O",
        "cas_number": "78-93-3",
        "un_number": "UN1193",
        "ghs_classes": ["FLAMMABLE_LIQUID", "EYE_IRRITANT"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "mek", "methyl ethyl ketone", "butanone", "2-butanone", "mek solvent",
            "ميثيل إيثيل كيتون", "ميثيل ايثيل كيتون", "مذيب mek", "بوتانون"
        ]
    },

    "CHEM-IPA": {
        "chemical_id": 8,
        "trade_name": "Isopropyl Alcohol 99.9% (IPA)",
        "chemical_name": "Isopropanol / 2-Propanol",
        "formula": "C3H8O",
        "cas_number": "67-63-0",
        "un_number": "UN1219",
        "ghs_classes": ["FLAMMABLE_LIQUID", "EYE_IRRITANT"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "isopropyl alcohol", "isopropanol", "ipa", "rubbing alcohol", "2-propanol",
            "كحول ايزوبروبيل", "ايزوبروبانول", "كحول نقي", "مذيب ipa"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 3. POLYMERS & CABLE MANUFACTURING RAW MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-PVC-RESIN": {
        "chemical_id": 9,
        "trade_name": "Suspension PVC Resin K-67",
        "chemical_name": "Polyvinyl Chloride",
        "formula": "(C2H3Cl)n",
        "cas_number": "9002-86-2",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["DUST_EXPLOSION_HAZARD"],
        "storage_class": "COMBUSTIBLE_SOLID",
        "keywords": [
            "pvc resin", "polyvinyl chloride", "pvc powder", "k67 pvc", "pvc compound",
            "حبيبات pvc", "بودرة pvc", "راتنج بي في سي", "بوليمر بي في سي", "خام pvc"
        ]
    },

    "CHEM-XLPE": {
        "chemical_id": 10,
        "trade_name": "Cross-Linked Polyethylene (XLPE) Compound",
        "chemical_name": "Silane / Peroxide Cross-linkable PE",
        "formula": "Polyethylene XL",
        "cas_number": "25213-02-9",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["THERMAL_DECOMPOSITION_HAZARD"],
        "storage_class": "COMBUSTIBLE_SOLID",
        "keywords": [
            "xlpe", "cross-linked polyethylene", "insulation compound", "peroxide xlpe", "silane xlpe",
            "بوليمر xlpe", "مادة عزل كابلات", "اكس ال بي اي", "حبيبات عزل كابلات"
        ]
    },

    "CHEM-DOP": {
        "chemical_id": 11,
        "trade_name": "Dioctyl Phthalate (DOP Plasticizer)",
        "chemical_name": "Bis(2-ethylhexyl) Phthalate",
        "formula": "C24H38O4",
        "cas_number": "117-81-7",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["REPRODUCTIVE_TOXICITY", "CARCINOGENICITY_2"],
        "storage_class": "ORGANIC_LIQUID",
        "keywords": [
            "dop", "dioctyl phthalate", "dehp", "plasticizer", "pvc plasticizer", "dotp",
            "ملين كيميائي dop", "داي اوكتيل فثالات", "بلاستيسايزر", "زيت تليين بي في سي"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 4. COMPRESSED INDUSTRIAL & HAZARDOUS GASES
    # ══════════════════════════════════════════════════════════════════════════

    "GAS-SF6": {
        "chemical_id": 12,
        "trade_name": "Sulfur Hexafluoride Gas (SF6)",
        "chemical_name": "Sulfur Hexafluoride",
        "formula": "SF6",
        "cas_number": "2551-62-4",
        "un_number": "UN1080",
        "ghs_classes": ["COMPRESSED_GAS", "ASPHYXIANT", "GREENHOUSE_GAS"],
        "storage_class": "COMPRESSED_GAS_NON_FLAMMABLE",
        "keywords": [
            "sf6", "sulfur hexafluoride", "switchgear gas", "dielectric gas", "gis gas",
            "غاز sf6", "سداسي فلوريد الكبريت", "غاز عزل المحطات", "غاز القواطع الكهربائية"
        ]
    },

    "GAS-H2S": {
        "chemical_id": 13,
        "trade_name": "Hydrogen Sulfide Toxic Gas",
        "chemical_name": "Hydrogen Sulfide",
        "formula": "H2S",
        "cas_number": "7783-06-4",
        "un_number": "UN1053",
        "ghs_classes": ["FLAMMABLE_GAS", "FATAL_INHALATION", "AQUATIC_ACUTE"],
        "storage_class": "TOXIC_FLAMMABLE_GAS",
        "keywords": [
            "h2s", "hydrogen sulfide", "sour gas", "sewer gas", "rotten egg gas",
            "غاز h2s", "كبريتيد الهيدروجين", "غاز كبريتيد الهيدروجين السام", "غاز البيض الفاسد"
        ]
    },

    "GAS-CO": {
        "chemical_id": 14,
        "trade_name": "Carbon Monoxide Gas",
        "chemical_name": "Carbon Monoxide",
        "formula": "CO",
        "cas_number": "630-08-0",
        "un_number": "UN1016",
        "ghs_classes": ["FLAMMABLE_GAS", "TOXIC_INHALATION", "REPRODUCTIVE_TOXICITY"],
        "storage_class": "TOXIC_FLAMMABLE_GAS",
        "keywords": [
            "carbon monoxide", "co gas", "silent killer", "combustion byproduct",
            "اول اكسيد الكربون", "أول أكسيد الكربون", "غاز co", "غاز الاحتراق السام"
        ]
    },

    "GAS-ARGON": {
        "chemical_id": 15,
        "trade_name": "Compressed Pure Argon Shielding Gas",
        "chemical_name": "Argon",
        "formula": "Ar",
        "cas_number": "7440-37-1",
        "un_number": "UN1006",
        "ghs_classes": ["COMPRESSED_GAS", "ASPHYXIANT"],
        "storage_class": "COMPRESSED_GAS_INERT",
        "keywords": [
            "argon", "argon gas", "welding shielding gas", "tig welding argon", "inert gas cylinder",
            "غاز ارجون", "غاز أرغون", "اسطوانة ارجون", "غاز لحام خامل"
        ]
    },

    "GAS-ACETYLENE": {
        "chemical_id": 16,
        "trade_name": "Dissolved Acetylene Gas",
        "chemical_name": "Ethyne / Acetylene",
        "formula": "C2H2",
        "cas_number": "74-86-2",
        "un_number": "UN1001",
        "ghs_classes": ["FLAMMABLE_GAS", "CHEMICALLY_UNSTABLE_GAS"],
        "storage_class": "FLAMMABLE_GAS",
        "keywords": [
            "acetylene", "ethyne", "dissolved acetylene", "oxy-acetylene welding gas", "gas cylinder acetylene",
            "اسيتيلين", "أسيتيلين", "غاز اللحام اسيتيلين", "اسطوانة اسيتيلين", "اوكسي اسيتيلين"
        ]
    },
}


def extract_chemical_info(text: str) -> Optional[Dict[str, Any]]:
    """
    Matches any chemical, solvent, industrial gas, or HazMat from user prompt
    in Arabic or English with synonym tolerance.
    """
    if not text:
        return None
    clean = normalize_text(text).lower()
    padded = f" {clean} "

    best_match = None
    max_len = 0

    for chem_code, info in CHEMICAL_REGISTRY.items():
        for kw in info["keywords"]:
            norm_kw = normalize_text(kw).lower()
            if f" {norm_kw} " in padded or norm_kw in clean:
                if len(norm_kw) > max_len:
                    max_len = len(norm_kw)
                    best_match = {
                        "chemical_code": chem_code,
                        "chemical_id": info.get("chemical_id"),
                        "trade_name": info.get("trade_name"),
                        "chemical_name": info.get("chemical_name"),
                        "formula": info.get("formula"),
                        "cas_number": info.get("cas_number"),
                        "un_number": info.get("un_number"),
                        "ghs_classes": info.get("ghs_classes", []),
                        "storage_class": info.get("storage_class"),
                        "matched_keyword": kw
                    }

    return best_match


def search_chemical_catalog(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Searches the chemical catalog by keyword query."""
    if not query:
        return []
    clean = normalize_text(query)
    results = []
    for code, info in CHEMICAL_REGISTRY.items():
        score = 0
        if clean in normalize_text(code):
            score += 10
        if clean in normalize_text(info.get("trade_name", "")):
            score += 8
        if clean in normalize_text(info.get("chemical_name", "")):
            score += 8
        if clean in normalize_text(info.get("formula", "")):
            score += 8
        if clean in normalize_text(info.get("cas_number", "")):
            score += 10
        for kw in info.get("keywords", []):
            if clean in normalize_text(kw):
                score += 5
                break
        if score > 0:
            results.append({"code": code, "score": score, **info})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
