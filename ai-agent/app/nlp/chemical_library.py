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

    "CHEM-HNO3": {
        "chemical_id": 3,
        "trade_name": "Nitric Acid 68% Technical",
        "chemical_name": "Nitric Acid / Aqua Fortis",
        "formula": "HNO3",
        "cas_number": "7697-37-2",
        "un_number": "UN2031",
        "ghs_classes": ["OXIDIZING_LIQUID", "CORROSIVE", "FATAL_INHALATION"],
        "storage_class": "OXIDIZING_ACID",
        "keywords": [
            "nitric acid", "hno3", "aqua fortis", "fuming nitric acid",
            "حمض النيتريك", "حمض نيتريك", "حمض الآزوت", "حمض ازوت"
        ]
    },

    "CHEM-H3PO4": {
        "chemical_id": 4,
        "trade_name": "Phosphoric Acid 85% Food/Industrial Grade",
        "chemical_name": "Orthophosphoric Acid",
        "formula": "H3PO4",
        "cas_number": "7664-38-2",
        "un_number": "UN1805",
        "ghs_classes": ["CORROSIVE", "SKIN_CORROSION"],
        "storage_class": "ACID_INORGANIC",
        "keywords": [
            "phosphoric acid", "h3po4", "orthophosphoric acid", "rust remover acid",
            "حمض الفوسفوريك", "حمض فوسفوريك", "حمض الفسفوريك", "فوسفوريك"
        ]
    },

    "CHEM-HF": {
        "chemical_id": 5,
        "trade_name": "Hydrofluoric Acid 48%",
        "chemical_name": "Hydrofluoric Acid",
        "formula": "HF",
        "cas_number": "7664-39-3",
        "un_number": "UN1790",
        "ghs_classes": ["FATAL_ORAL", "FATAL_DERMAL", "FATAL_INHALATION", "CORROSIVE"],
        "storage_class": "ACID_INORGANIC_TOXIC",
        "keywords": [
            "hydrofluoric acid", "hf", "hydrogen fluoride solution", "glass etching acid",
            "حمض الهيدروفلوريك", "حمض هيدروفلوريك", "هيدروفلوريك", "حمض الفلوريك"
        ]
    },

    "CHEM-CH3COOH": {
        "chemical_id": 6,
        "trade_name": "Glacial Acetic Acid 99.8%",
        "chemical_name": "Ethanoic Acid / Acetic Acid",
        "formula": "CH3COOH",
        "cas_number": "64-19-7",
        "un_number": "UN2789",
        "ghs_classes": ["FLAMMABLE_LIQUID", "CORROSIVE"],
        "storage_class": "ACID_ORGANIC_FLAMMABLE",
        "keywords": [
            "acetic acid", "glacial acetic acid", "ethanoic acid", "vinegar acid",
            "حمض الخليك", "حمض خليك", "حمض الخليك الثلجي", "حمض الاسيتيك", "حمض إيثانويك"
        ]
    },

    "CHEM-CITRIC": {
        "chemical_id": 7,
        "trade_name": "Citric Acid Anhydrous",
        "chemical_name": "2-Hydroxypropane-1,2,3-tricarboxylic acid",
        "formula": "C6H8O7",
        "cas_number": "77-92-9",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["EYE_IRRITANT"],
        "storage_class": "ORGANIC_SOLID",
        "keywords": [
            "citric acid", "anhydrous citric acid", "descaling acid",
            "حمض الستريك", "حمض ستريك", "ملح ليمون", "ملح الليمون", "حمض الليمون"
        ]
    },

    "CHEM-NAOH": {
        "chemical_id": 8,
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

    "CHEM-KOH": {
        "chemical_id": 9,
        "trade_name": "Potassium Hydroxide Flakes (KOH)",
        "chemical_name": "Potassium Hydroxide / Caustic Potash",
        "formula": "KOH",
        "cas_number": "1310-58-3",
        "un_number": "UN1813",
        "ghs_classes": ["CORROSIVE", "ACUTE_TOXICITY"],
        "storage_class": "BASE_INORGANIC",
        "keywords": [
            "potassium hydroxide", "koh", "caustic potash", "potash lye",
            "هيدروكسيد البوتاسيوم", "هيدروكسيد بوتاسيوم", "بوتاس كاوية", "بوتاس"
        ]
    },

    "CHEM-NH4OH": {
        "chemical_id": 10,
        "trade_name": "Ammonia Solution 25% (Ammonium Hydroxide)",
        "chemical_name": "Ammonium Hydroxide Aqueous",
        "formula": "NH4OH",
        "cas_number": "1336-21-6",
        "un_number": "UN2672",
        "ghs_classes": ["CORROSIVE", "AQUATIC_ACUTE_1", "ACUTE_TOXICITY"],
        "storage_class": "BASE_INORGANIC",
        "keywords": [
            "ammonium hydroxide", "ammonia solution", "aqua ammonia", "nh4oh",
            "هيدروكسيد الامونيوم", "هيدروكسيد الأمونيوم", "محلول النشادر", "ماء النشادر", "امونيا سائلة"
        ]
    },

    "CHEM-CAOH2": {
        "chemical_id": 11,
        "trade_name": "Hydrated Lime (Calcium Hydroxide)",
        "chemical_name": "Calcium Hydroxide / Slaked Lime",
        "formula": "Ca(OH)2",
        "cas_number": "1305-62-0",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["CORROSIVE", "EYE_DAMAGE"],
        "storage_class": "BASE_INORGANIC",
        "keywords": [
            "calcium hydroxide", "slaked lime", "hydrated lime", "ca(oh)2",
            "هيدروكسيد الكالسيوم", "الجير المطفأ", "جير مطفأ", "شيد"
        ]
    },

    "CHEM-NA2CO3": {
        "chemical_id": 12,
        "trade_name": "Dense Soda Ash (Sodium Carbonate)",
        "chemical_name": "Sodium Carbonate Anhydrous",
        "formula": "Na2CO3",
        "cas_number": "497-19-8",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["EYE_IRRITANT"],
        "storage_class": "INORGANIC_SOLID",
        "keywords": [
            "sodium carbonate", "soda ash", "washing soda", "na2co3",
            "كربونات الصوديوم", "صودا اش", "رماد الصودا", "زهرة الغسيل"
        ]
    },

    "CHEM-NAHCO3": {
        "chemical_id": 13,
        "trade_name": "Sodium Bicarbonate Technical Grade",
        "chemical_name": "Sodium Hydrogen Carbonate / Baking Soda",
        "formula": "NaHCO3",
        "cas_number": "144-55-8",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "INORGANIC_SOLID",
        "keywords": [
            "sodium bicarbonate", "baking soda", "nahco3", "sodium hydrogen carbonate",
            "بيكربونات الصوديوم", "كربونات الصوديوم الهيدروجينية", "كربوناتو", "بيكربونات"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 2. INDUSTRIAL SOLVENTS, ALCOHOLS & DEGREASERS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-ETHANOL": {
        "chemical_id": 14,
        "trade_name": "Industrial Denatured Ethanol 96%",
        "chemical_name": "Ethyl Alcohol / Ethanol",
        "formula": "C2H5OH",
        "cas_number": "64-17-5",
        "un_number": "UN1170",
        "ghs_classes": ["FLAMMABLE_LIQUID", "EYE_IRRITANT"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "ethanol", "ethyl alcohol", "ethylalcohol", "grain alcohol", "industrial alcohol", "denatured ethanol",
            "absolute ethanol", "ethyl hydrate", "alcohol ethyl", "c2h5oh",
            "ايثايل الكحول", "إيثايل الكحول", "ايثيل الكحول", "إيثيل الكحول", "ايثايل كحول", "ايثيل كحول",
            "كحول ايثايل", "كحول ايثيل", "كحول الإيثايل", "كحول الإيثيل", "كحول الايثيل", "كحول الايثايل",
            "الكحول الإيثيلي", "الكحول الايثيلي", "كحول إيثيلي", "كحول ايثيلي", "إيثانول", "ايثانول",
            "إيثيل ألكوهول", "ايثيل الكوهول", "كحول أبيض", "كحول ابيض", "كحول نقي", "سبيرتو", "سبرتو",
            "كحول صناعي", "مذيب كحول", "مادة كحول", "ماده كحول"
        ]
    },

    "CHEM-METHANOL": {
        "chemical_id": 15,
        "trade_name": "Pure Methanol Industrial Grade",
        "chemical_name": "Methanol / Methyl Alcohol",
        "formula": "CH3OH",
        "cas_number": "67-56-1",
        "un_number": "UN1230",
        "ghs_classes": ["FLAMMABLE_LIQUID", "ACUTE_TOXICITY", "STOT_SE_1"],
        "storage_class": "FLAMMABLE_TOXIC_ORGANIC",
        "keywords": [
            "methanol", "methyl alcohol", "wood alcohol", "carbinol", "ch3oh",
            "ميثانول", "كحول ميثيلي", "ميثايل الكحول", "ميثيل الكحول", "كحول الميثيل", "الكحول الميثيلي", "كحول الخشب"
        ]
    },

    "CHEM-IPA": {
        "chemical_id": 16,
        "trade_name": "Isopropyl Alcohol 99.9% (IPA)",
        "chemical_name": "Isopropanol / 2-Propanol",
        "formula": "C3H8O",
        "cas_number": "67-63-0",
        "un_number": "UN1219",
        "ghs_classes": ["FLAMMABLE_LIQUID", "EYE_IRRITANT", "STOT_SE_3"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "isopropyl alcohol", "isopropanol", "ipa", "rubbing alcohol", "2-propanol",
            "كحول ايزوبروبيل", "ايزوبروبانول", "كحول نقي", "مذيب ipa", "كحول ايزوبروبيلي", "ايزوبروبيل"
        ]
    },

    "CHEM-ACETONE": {
        "chemical_id": 17,
        "trade_name": "Pure Acetone Technical Grade",
        "chemical_name": "Propan-2-one / Acetone",
        "formula": "C3H6O",
        "cas_number": "67-64-1",
        "un_number": "UN1090",
        "ghs_classes": ["FLAMMABLE_LIQUID", "EYE_IRRITANT", "STOT_SE_3"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "acetone", "propanone", "dimethyl ketone", "cleaning solvent acetone",
            "اسيتون", "أسيتون", "مذيب اسيتون", "بروبانون"
        ]
    },

    "CHEM-TOLUENE": {
        "chemical_id": 18,
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
        "chemical_id": 19,
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

    "CHEM-MEK": {
        "chemical_id": 20,
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

    "CHEM-ETHYL-ACETATE": {
        "chemical_id": 21,
        "trade_name": "Ethyl Acetate Pure Grade",
        "chemical_name": "Ethyl Ethanoate",
        "formula": "C4H8O2",
        "cas_number": "141-78-6",
        "un_number": "UN1173",
        "ghs_classes": ["FLAMMABLE_LIQUID", "EYE_IRRITANT", "STOT_SE_3"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "ethyl acetate", "ethyl ethanoate", "acetidin",
            "إيثيل أسيتات", "ايثيل اسيتات", "خلات الإيثيل", "خلات الايثيل"
        ]
    },

    "CHEM-BUTYL-ACETATE": {
        "chemical_id": 22,
        "trade_name": "n-Butyl Acetate Solvent",
        "chemical_name": "Butyl Ethanoate",
        "formula": "C6H12O2",
        "cas_number": "123-86-4",
        "un_number": "UN1123",
        "ghs_classes": ["FLAMMABLE_LIQUID", "STOT_SE_3"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "butyl acetate", "n-butyl acetate", "butyl ethanoate",
            "بيوتيل أسيتات", "بيوتيل اسيتات", "خلات البيوتيل"
        ]
    },

    "CHEM-THF": {
        "chemical_id": 23,
        "trade_name": "Tetrahydrofuran (THF) Pure",
        "chemical_name": "Tetrahydrofuran / Oxolane",
        "formula": "C4H8O",
        "cas_number": "109-99-9",
        "un_number": "UN2056",
        "ghs_classes": ["FLAMMABLE_LIQUID", "CARCINOGENICITY_2", "EYE_DAMAGE"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "thf", "tetrahydrofuran", "oxolane", "pvc welding solvent",
            "تتراهيدروفيوران", "مذيب thf", "رباعي هيدرو فيوران"
        ]
    },

    "CHEM-DCM": {
        "chemical_id": 24,
        "trade_name": "Methylene Chloride (Dichloromethane / DCM)",
        "chemical_name": "Dichloromethane",
        "formula": "CH2Cl2",
        "cas_number": "75-09-2",
        "un_number": "UN1593",
        "ghs_classes": ["CARCINOGENICITY_2", "ACUTE_TOXICITY", "STOT_SE_3"],
        "storage_class": "TOXIC_HALOGENATED_SOLVENT",
        "keywords": [
            "dcm", "methylene chloride", "dichloromethane", "paint stripper dcm",
            "ميثيلين كلورايد", "ثنائي كلورو ميثان", "مذيب dcm", "مزيل الدهان"
        ]
    },

    "CHEM-TCE": {
        "chemical_id": 25,
        "trade_name": "Trichloroethylene (TCE Degreaser)",
        "chemical_name": "Trichloroethene",
        "formula": "C2HCl3",
        "cas_number": "79-01-6",
        "un_number": "UN1710",
        "ghs_classes": ["CARCINOGENICITY_1B", "MUTAGENICITY_2", "ACUTE_TOXICITY"],
        "storage_class": "TOXIC_HALOGENATED_SOLVENT",
        "keywords": [
            "tce", "trichloroethylene", "triklone", "metal degreaser tce",
            "ثلاثي كلورو إيثيلين", "ترايكلوروايثيلين", "مذيب تسي اي"
        ]
    },

    "CHEM-WHITE-SPIRIT": {
        "chemical_id": 26,
        "trade_name": "Industrial White Spirit / Mineral Spirits",
        "chemical_name": "Hydrocarbons, C9-C12, n-alkanes, isoalkanes",
        "formula": "Hydrocarbon Mixture",
        "cas_number": "64742-82-1",
        "un_number": "UN1300",
        "ghs_classes": ["FLAMMABLE_LIQUID", "ASPIRATION_HAZARD", "STOT_RE"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "white spirit", "mineral spirits", "stoddard solvent", "turpentine substitute", "paint thinner",
            "وايت سبيريت", "وايت سبرت", "نفط معدني", "تنر", "مذيب دهانات"
        ]
    },

    "CHEM-HEXANE": {
        "chemical_id": 27,
        "trade_name": "n-Hexane Solvent Grade",
        "chemical_name": "Hexane",
        "formula": "C6H14",
        "cas_number": "110-54-3",
        "un_number": "UN1208",
        "ghs_classes": ["FLAMMABLE_LIQUID", "REPRODUCTIVE_TOXICITY", "ASPIRATION_HAZARD"],
        "storage_class": "FLAMMABLE_ORGANIC",
        "keywords": [
            "hexane", "n-hexane", "extraction solvent",
            "هكسان", "ان هكسان", "مذيب الهكسان"
        ]
    },

    "CHEM-ETHYLENE-GLYCOL": {
        "chemical_id": 28,
        "trade_name": "Monoethylene Glycol (MEG Antifreeze)",
        "chemical_name": "Ethane-1,2-diol",
        "formula": "C2H6O2",
        "cas_number": "107-21-1",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["ACUTE_TOXICITY_4", "STOT_RE_2"],
        "storage_class": "ORGANIC_LIQUID",
        "keywords": [
            "ethylene glycol", "meg", "antifreeze", "chiller coolant",
            "ايثيلين جليكول", "إيثيلين جليكول", "مياه مبردات", "مانع تجمد"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 3. CABLE MANUFACTURING POLYMERS, ADDITIVES & RAW MATERIALS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-PVC-RESIN": {
        "chemical_id": 29,
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
        "chemical_id": 30,
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

    "CHEM-HDPE": {
        "chemical_id": 31,
        "trade_name": "High-Density Polyethylene (HDPE Cable Sheathing)",
        "chemical_name": "Polyethylene High Density",
        "formula": "(C2H4)n",
        "cas_number": "9002-88-4",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "COMBUSTIBLE_SOLID",
        "keywords": [
            "hdpe", "high density polyethylene", "cable sheathing pe",
            "بولي إيثيلين عالي الكثافة", "بولي ايثيلين عالي الكثافة", "خام hdpe"
        ]
    },

    "CHEM-LDPE": {
        "chemical_id": 32,
        "trade_name": "Low-Density Polyethylene (LDPE)",
        "chemical_name": "Polyethylene Low Density",
        "formula": "(C2H4)n",
        "cas_number": "9002-88-4",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "COMBUSTIBLE_SOLID",
        "keywords": [
            "ldpe", "low density polyethylene", "بولي إيثيلين منخفض الكثافة", "خام ldpe"
        ]
    },

    "CHEM-LSZH": {
        "chemical_id": 33,
        "trade_name": "Low Smoke Zero Halogen (LSZH / HFFR Compound)",
        "chemical_name": "Halogen-Free Flame Retardant Compound",
        "formula": "Polymer + ATH/MDH",
        "cas_number": "9002-88-4",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "COMBUSTIBLE_SOLID",
        "keywords": [
            "lszh", "hffr", "low smoke zero halogen", "fire resistant cable compound",
            "مادة عزل lszh", "عزل مقاوم للحريق خالي من الهالوجين", "حبيبات hffr"
        ]
    },

    "CHEM-ATH": {
        "chemical_id": 34,
        "trade_name": "Aluminum Trihydrate Flame Retardant (ATH)",
        "chemical_name": "Aluminum Hydroxide / ATH",
        "formula": "Al(OH)3",
        "cas_number": "21645-51-2",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "INORGANIC_SOLID",
        "keywords": [
            "ath", "aluminum trihydrate", "aluminium hydroxide flame retardant",
            "ألومنيوم ثلاثي الهيدرات", "الومنيوم ثلاثي الهيدرات", "مانع اشتعال ath"
        ]
    },

    "CHEM-DOP": {
        "chemical_id": 35,
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

    "CHEM-DOTP": {
        "chemical_id": 36,
        "trade_name": "Dioctyl Terephthalate (DOTP Eco-Plasticizer)",
        "chemical_name": "Bis(2-ethylhexyl) Terephthalate",
        "formula": "C24H38O4",
        "cas_number": "6422-86-2",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "ORGANIC_LIQUID",
        "keywords": [
            "dotp", "dioctyl terephthalate", "non-phthalate plasticizer", "eco plasticizer",
            "ملين بيئي dotp", "داي اوكتيل تيريفثالات"
        ]
    },

    "CHEM-LEAD-STABILIZER": {
        "chemical_id": 37,
        "trade_name": "Tribasic Lead Sulfate (TBLS PVC Stabilizer)",
        "chemical_name": "Lead Oxide Sulfate Trihydrate",
        "formula": "3PbO.PbSO4.H2O",
        "cas_number": "12202-17-4",
        "un_number": "UN2291",
        "ghs_classes": ["FATAL_ORAL", "REPRODUCTIVE_TOXICITY", "CARCINOGENICITY_2"],
        "storage_class": "TOXIC_SOLID_INORGANIC",
        "keywords": [
            "tbls", "lead stabilizer", "tribasic lead sulfate", "pvc thermal stabilizer",
            "مثبت رصاص", "سلفات الرصاص ثلاثية القاعدة", "مثبت حراري بي في سي"
        ]
    },

    "CHEM-CAZN-STABILIZER": {
        "chemical_id": 38,
        "trade_name": "Calcium-Zinc (Ca/Zn) Non-Toxic Cable Stabilizer",
        "chemical_name": "Calcium Zinc Stearate Complex",
        "formula": "Ca-Zn Complex",
        "cas_number": "1592-23-0",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "INORGANIC_SOLID",
        "keywords": [
            "ca/zn stabilizer", "calcium zinc stabilizer", "non-toxic pvc stabilizer",
            "مثبت كالسيوم زنك", "مثبت بيئي غير سام"
        ]
    },

    "CHEM-CARBON-BLACK": {
        "chemical_id": 39,
        "trade_name": "Carbon Black UV-Protective Masterbatch",
        "chemical_name": "Carbon Black / Acetylene Black",
        "formula": "C",
        "cas_number": "1333-86-4",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["CARCINOGENICITY_2", "DUST_EXPLOSION_HAZARD"],
        "storage_class": "COMBUSTIBLE_SOLID",
        "keywords": [
            "carbon black", "uv masterbatch", "black pigment", "carbon masterbatch",
            "كربون بلاك", "ماسترباتش اسود", "اسود الكربون", "صبغة كربونية"
        ]
    },

    "CHEM-TIO2": {
        "chemical_id": 40,
        "trade_name": "Titanium Dioxide (Rutile TiO2 White Pigment)",
        "chemical_name": "Titanium Dioxide",
        "formula": "TiO2",
        "cas_number": "13463-67-7",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["CARCINOGENICITY_2"],
        "storage_class": "INORGANIC_SOLID",
        "keywords": [
            "titanium dioxide", "tio2", "rutile white pigment", "white masterbatch",
            "ثاني أكسيد التيتانيوم", "ثاني اكسيد التيتانيوم", "صبغة بيضاء tio2"
        ]
    },

    "CHEM-CACO3": {
        "chemical_id": 41,
        "trade_name": "Precipitated Calcium Carbonate (PCC/GCC Filler)",
        "chemical_name": "Calcium Carbonate",
        "formula": "CaCO3",
        "cas_number": "471-34-1",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "INORGANIC_SOLID",
        "keywords": [
            "calcium carbonate", "caco3", "pcc filler", "calcite powder", "cable filler",
            "كربونات الكالسيوم", "بودرة كربونات كالسيوم", "فيلر كابلات"
        ]
    },

    "CHEM-DCP": {
        "chemical_id": 42,
        "trade_name": "Dicumyl Peroxide (DCP Cross-Linking Catalyst)",
        "chemical_name": "Bis(1-methyl-1-phenylethyl) Peroxide",
        "formula": "C18H22O2",
        "cas_number": "80-43-3",
        "un_number": "UN3110",
        "ghs_classes": ["ORGANIC_PEROXIDE", "SKIN_IRRITANT", "AQUATIC_CHRONIC_2"],
        "storage_class": "ORGANIC_PEROXIDE",
        "keywords": [
            "dcp", "dicumyl peroxide", "xlpe crosslinking agent", "peroxide initiator",
            "دايكوميل بيروكسيد", "عامل تشابك dcp", "بادئ بلمرة"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 4. METALS & CABLE CONDUCTORS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-COPPER": {
        "chemical_id": 43,
        "trade_name": "Electrolytic Copper Continuous Cast Rod (Cu-ETP)",
        "chemical_name": "Copper Metal 99.99%",
        "formula": "Cu",
        "cas_number": "7440-50-8",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "METALS_NON_COMBUSTIBLE",
        "keywords": [
            "copper", "copper rod", "cu-etp", "electrolytic copper", "conductor wire",
            "نحاس", "نحاس الكتروليتي", "قضبان نحاس", "سلك نحاس", "خام نحاس"
        ]
    },

    "CHEM-ALUMINUM": {
        "chemical_id": 44,
        "trade_name": "EC Grade Aluminum Rod 1350/Alloy",
        "chemical_name": "Aluminum Metal",
        "formula": "Al",
        "cas_number": "7429-90-5",
        "un_number": "UN1396",
        "ghs_classes": ["WATER_REACTIVE_FLAMMABLE_DUST"],
        "storage_class": "METALS_POWDER_HAZARD",
        "keywords": [
            "aluminum", "aluminium", "aluminum rod", "ec aluminum", "al conductor",
            "ألومنيوم", "الومنيوم", "قضبان الومنيوم", "سلك الومنيوم", "خام الومنيوم"
        ]
    },

    "CHEM-LEAD-METAL": {
        "chemical_id": 45,
        "trade_name": "Refined Lead Ingot (Cable Sheathing Alloy)",
        "chemical_name": "Lead Metal",
        "formula": "Pb",
        "cas_number": "7439-92-1",
        "un_number": "UN3077",
        "ghs_classes": ["REPRODUCTIVE_TOXICITY", "CARCINOGENICITY_2", "STOT_RE_1"],
        "storage_class": "TOXIC_SOLID_INORGANIC",
        "keywords": [
            "lead ingot", "metallic lead", "lead cable sheath", "pb metal",
            "رصاص", "سبائك رصاص", "غلاف رصاص", "معدن الرصاص"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 5. COMPRESSED INDUSTRIAL & HAZARDOUS GASES
    # ══════════════════════════════════════════════════════════════════════════

    "GAS-SF6": {
        "chemical_id": 46,
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
        "chemical_id": 47,
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
        "chemical_id": 48,
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
        "chemical_id": 49,
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
        "chemical_id": 50,
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

    "GAS-OXYGEN": {
        "chemical_id": 51,
        "trade_name": "Compressed Industrial Oxygen (O2)",
        "chemical_name": "Oxygen",
        "formula": "O2",
        "cas_number": "7782-44-7",
        "un_number": "UN1072",
        "ghs_classes": ["OXIDIZING_GAS", "COMPRESSED_GAS"],
        "storage_class": "OXIDIZING_GAS",
        "keywords": [
            "oxygen", "o2 gas", "industrial oxygen", "cutting oxygen", "oxygen cylinder",
            "اكسجين", "أكسجين", "غاز اكسجين", "اسطوانة اكسجين"
        ]
    },

    "GAS-NITROGEN": {
        "chemical_id": 52,
        "trade_name": "Compressed Pure Nitrogen Gas (N2)",
        "chemical_name": "Nitrogen",
        "formula": "N2",
        "cas_number": "7727-37-9",
        "un_number": "UN1066",
        "ghs_classes": ["COMPRESSED_GAS", "ASPHYXIANT"],
        "storage_class": "COMPRESSED_GAS_INERT",
        "keywords": [
            "nitrogen", "n2 gas", "inert nitrogen", "purging gas", "nitrogen cylinder",
            "نيتروجين", "غاز نيتروجين", "اسطوانة نيتروجين", "غاز خامل نيتروجين"
        ]
    },

    "GAS-CO2": {
        "chemical_id": 53,
        "trade_name": "Carbon Dioxide Liquid/Gas (CO2)",
        "chemical_name": "Carbon Dioxide",
        "formula": "CO2",
        "cas_number": "124-38-9",
        "un_number": "UN1013",
        "ghs_classes": ["COMPRESSED_GAS", "ASPHYXIANT"],
        "storage_class": "COMPRESSED_GAS_INERT",
        "keywords": [
            "co2", "carbon dioxide", "fire suppression co2", "dry ice",
            "ثاني أكسيد الكربون", "ثاني اكسيد الكربون", "غاز co2", "اسطوانة ثاني اكسيد الكربون"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 6. CYANIDES & HIGHLY TOXIC CHEMICALS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-CACN2": {
        "chemical_id": 54,
        "trade_name": "Calcium Cyanide Solid 95%",
        "chemical_name": "Calcium Cyanide / Calcyanide",
        "formula": "Ca(CN)2",
        "cas_number": "592-01-8",
        "un_number": "UN1575",
        "ghs_classes": ["FATAL_ORAL", "FATAL_DERMAL", "FATAL_INHALATION", "AQUATIC_ACUTE_1"],
        "storage_class": "TOXIC_SOLID_INORGANIC",
        "keywords": [
            "calcium cyanide", "calcuim cianade", "calcium cianide", "calcuim cyanide", "calcum cyanide",
            "ca(cn)2", "calcyanide", "cyanide of calcium", "cyanide", "cianade", "cianide",
            "سيانيد الكالسيوم", "سيانيد كالسيوم", "مادة سيانيد الكالسيوم", "سيانيد", "سم سيانيد الكالسيوم"
        ]
    },

    "CHEM-NACN": {
        "chemical_id": 55,
        "trade_name": "Sodium Cyanide Briquettes 98%",
        "chemical_name": "Sodium Cyanide",
        "formula": "NaCN",
        "cas_number": "143-33-9",
        "un_number": "UN1689",
        "ghs_classes": ["FATAL_ORAL", "FATAL_DERMAL", "FATAL_INHALATION", "AQUATIC_ACUTE_1"],
        "storage_class": "TOXIC_SOLID_INORGANIC",
        "keywords": [
            "sodium cyanide", "nacn", "cyanogran", "sodium cianide",
            "سيانيد الصوديوم", "سيانيد صوديوم", "مركب سيانيد الصوديوم"
        ]
    },

    "CHEM-KCN": {
        "chemical_id": 56,
        "trade_name": "Potassium Cyanide Pure Grade",
        "chemical_name": "Potassium Cyanide",
        "formula": "KCN",
        "cas_number": "151-50-8",
        "un_number": "UN1680",
        "ghs_classes": ["FATAL_ORAL", "FATAL_DERMAL", "FATAL_INHALATION", "AQUATIC_ACUTE_1"],
        "storage_class": "TOXIC_SOLID_INORGANIC",
        "keywords": [
            "potassium cyanide", "kcn", "potassium cianide",
            "سيانيد البوتاسيوم", "سيانيد بوتاسيوم"
        ]
    },

    "CHEM-HCN": {
        "chemical_id": 57,
        "trade_name": "Hydrogen Cyanide (Prussic Acid)",
        "chemical_name": "Hydrocyanic Acid / Formonitrile",
        "formula": "HCN",
        "cas_number": "74-90-8",
        "un_number": "UN1051",
        "ghs_classes": ["FATAL_ORAL", "FATAL_DERMAL", "FATAL_INHALATION", "FLAMMABLE_LIQUID"],
        "storage_class": "TOXIC_FLAMMABLE_LIQUID",
        "keywords": [
            "hydrogen cyanide", "prussic acid", "formonitrile", "hcn gas",
            "سيانيد الهيدروجين", "حمض الهيدروسيانيك", "غاز السيانيد"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 7. OXIDIZERS & BLEACHING AGENTS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-H2O2": {
        "chemical_id": 58,
        "trade_name": "Hydrogen Peroxide 50% Technical",
        "chemical_name": "Hydrogen Peroxide Solution",
        "formula": "H2O2",
        "cas_number": "7722-84-1",
        "un_number": "UN2014",
        "ghs_classes": ["OXIDIZING_LIQUID", "CORROSIVE", "ACUTE_TOXICITY"],
        "storage_class": "OXIDIZER_LIQUID",
        "keywords": [
            "hydrogen peroxide", "h2o2", "peroxide", "bleaching agent",
            "فوق أكسيد الهيدروجين", "بيروكسيد الهيدروجين", "ماء أكسجين", "مية اكسجين"
        ]
    },

    "CHEM-NAOCL": {
        "chemical_id": 59,
        "trade_name": "Sodium Hypochlorite 12% (Industrial Bleach)",
        "chemical_name": "Sodium Hypochlorite Aqueous",
        "formula": "NaOCl",
        "cas_number": "7681-52-9",
        "un_number": "UN1791",
        "ghs_classes": ["CORROSIVE", "AQUATIC_ACUTE_1", "SKIN_CORROSION"],
        "storage_class": "CORROSIVE_OXIDIZER",
        "keywords": [
            "sodium hypochlorite", "naocl", "liquid chlorine", "industrial bleach",
            "هيبوكلوريت الصوديوم", "كلور سائل", "مبيض كلور", "كلوركس صناعي"
        ]
    },

    "CHEM-KMNO4": {
        "chemical_id": 60,
        "trade_name": "Potassium Permanganate Crystals",
        "chemical_name": "Potassium Manganate(VII)",
        "formula": "KMnO4",
        "cas_number": "7722-64-7",
        "un_number": "UN1490",
        "ghs_classes": ["OXIDIZING_SOLID", "ACUTE_TOXICITY", "AQUATIC_ACUTE_1"],
        "storage_class": "OXIDIZER_INORGANIC",
        "keywords": [
            "potassium permanganate", "kmno4", "permanganate of potash",
            "برمنجنات البوتاسيوم", "برمنجانات", "برمنجنات"
        ]
    },

    "CHEM-NA2O5": {
        "chemical_id": 61,
        "trade_name": "Sodium Pentoxide (Na2O5)",
        "chemical_name": "Sodium Pentoxide",
        "formula": "Na2O5",
        "cas_number": "12034-11-6",
        "un_number": "UN1479",
        "ghs_classes": ["OXIDIZING_SOLID", "CORROSIVE"],
        "storage_class": "OXIDIZER_INORGANIC",
        "keywords": [
            "sodium pentoxide", "na2o5", "sodium pentaoxide",
            "صوديوم بنتا أوكسايد", "صوديوم بنتا اوكسايد", "صوديوم بنتاأوكسيد", "صوديوم بنتا اوكسيد"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 8. OILS, LUBRICANTS, COOLANTS & DIELECTRICS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-TRANSFORMER-OIL": {
        "chemical_id": 62,
        "trade_name": "High-Voltage Transformer Dielectric Mineral Oil",
        "chemical_name": "Hydrotreated Light Naphthenic Distillate",
        "formula": "Mineral Hydrocarbon",
        "cas_number": "64742-53-6",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["ASPIRATION_HAZARD"],
        "storage_class": "COMBUSTIBLE_LIQUID",
        "keywords": [
            "transformer oil", "dielectric oil", "insulating oil", "mineral oil", "switchgear oil",
            "زيت المحولات", "زيت محولات", "زيت عزل المحولات", "زيت المحول الكهربائي", "زيت قواطع"
        ]
    },

    "CHEM-DRAWING-LUBRICANT": {
        "chemical_id": 63,
        "trade_name": "Copper/Aluminum Wire Drawing Emulsion Lubricant",
        "chemical_name": "Soluble Fatty Ester / Emulsifiable Oil",
        "formula": "Emulsion",
        "cas_number": "64742-52-5",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["EYE_IRRITANT"],
        "storage_class": "COMBUSTIBLE_LIQUID",
        "keywords": [
            "drawing lubricant", "wire drawing oil", "copper drawing emulsion", "rod breakdown oil",
            "زيت سحب الأسلاك", "زيت سحب النحاس", "مستحلب سحب الأسلاك", "زيت دراوينج"
        ]
    },

    "CHEM-HYDRAULIC-OIL": {
        "chemical_id": 64,
        "trade_name": "Industrial Hydraulic Oil ISO VG 46/68",
        "chemical_name": "Severely Hydrotreated Mineral Oil + Anti-Wear Additives",
        "formula": "Hydrocarbon Mixture",
        "cas_number": "64742-54-7",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "COMBUSTIBLE_LIQUID",
        "keywords": [
            "hydraulic oil", "hydraulic fluid", "iso vg 46", "iso vg 68", "anti-wear hydraulic oil",
            "زيت هيدروليك", "زيت هيدروليكي", "زيت مكابس", "زيت رافعات"
        ]
    },

    "CHEM-GEAR-OIL": {
        "chemical_id": 65,
        "trade_name": "Industrial Heavy-Duty Gear Oil ISO VG 220/320",
        "chemical_name": "Industrial Extreme Pressure Gear Lubricant",
        "formula": "Hydrocarbon Mixture",
        "cas_number": "64742-54-7",
        "un_number": "NON_REGULATED",
        "ghs_classes": [],
        "storage_class": "COMBUSTIBLE_LIQUID",
        "keywords": [
            "gear oil", "gearbox lubricant", "iso vg 220", "iso vg 320", "ep gear oil",
            "زيت تروس", "زيت جيربوكس", "زيت تروس صناعية", "زيت فتيس"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 9. WATER TREATMENT & EFFLUENT CHEMICALS
    # ══════════════════════════════════════════════════════════════════════════

    "CHEM-FECL3": {
        "chemical_id": 66,
        "trade_name": "Ferric Chloride 40% Coagulant Solution",
        "chemical_name": "Iron(III) Chloride Aqueous",
        "formula": "FeCl3",
        "cas_number": "7705-08-0",
        "un_number": "UN2582",
        "ghs_classes": ["CORROSIVE", "ACUTE_TOXICITY", "SKIN_IRRITANT"],
        "storage_class": "ACID_INORGANIC_CORROSIVE",
        "keywords": [
            "ferric chloride", "fecl3", "iron chloride coagulant", "water treatment coagulant",
            "كلوريد الحديديك", "مخثر كلوريد الحديديك", "معالجة مياه الصرف"
        ]
    },

    "CHEM-PAC": {
        "chemical_id": 67,
        "trade_name": "Polyaluminum Chloride (PAC 30% Powder)",
        "chemical_name": "Aluminum Chlorohydrate Complex",
        "formula": "[Al2(OH)nCl6-n]m",
        "cas_number": "1327-41-9",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["CORROSIVE", "EYE_DAMAGE"],
        "storage_class": "INORGANIC_SOLID",
        "keywords": [
            "pac", "polyaluminum chloride", "flocculant pac", "water clarifying pac",
            "بولي ألومنيوم كلورايد", "مروق pac", "مخثر مياه"
        ]
    },

    "CHEM-SMBS": {
        "chemical_id": 68,
        "trade_name": "Sodium Metabisulfite Food/Industrial Grade",
        "chemical_name": "Sodium Pyrosulfite / SMBS",
        "formula": "Na2S2O5",
        "cas_number": "7681-57-4",
        "un_number": "NON_REGULATED",
        "ghs_classes": ["ACUTE_TOXICITY_4", "EYE_DAMAGE"],
        "storage_class": "INORGANIC_SOLID",
        "keywords": [
            "sodium metabisulfite", "smbs", "dechlorination agent", "antioxidant smbs",
            "ميتابيسلفيت الصوديوم", "صوديوم ميتابايسلفيت", "مزيل الكلور"
        ]
    },
}


_TYPO_NORMALIZATION_MAP = {
    "calcuim": "calcium",
    "calcum": "calcium",
    "cianade": "cyanide",
    "cianide": "cyanide",
    "sianide": "cyanide",
    "sulferic": "sulfuric",
    "sulphuric": "sulfuric",
    "hyrdo": "hydro",
    "aceton": "acetone",
    "toluen": "toluene",
    "xylen": "xylene",
    "pottasium": "potassium",
    "potasium": "potassium",
    "soduim": "sodium",
    "nitrik": "nitric",
    "phosforic": "phosphoric",
    "ethyle": "ethyl",
    "ethil": "ethyl",
    "ethly": "ethyl",
    "ايثايل": "ايثانول",
    "ايثيل": "ايثانول",
    "إيثايل": "ايثانول",
    "إيثيل": "ايثانول",
    "ميثايل": "ميثانول",
    "ميثيل": "ميثانول",
    "الكوهول": "كحول",
    "الكهول": "كحول",
    "الكوحل": "كحول",
    "ألكوهول": "كحول",
}


def _normalize_chemical_query(text: str) -> str:
    """Normalizes common typos and transliterations in chemical inquiries."""
    clean = normalize_text(text).lower()
    words = clean.split()
    fixed_words = [_TYPO_NORMALIZATION_MAP.get(w, w) for w in words]
    return " ".join(fixed_words)


def extract_chemical_info(text: str) -> Optional[Dict[str, Any]]:
    """
    Matches any chemical, solvent, industrial gas, or HazMat from user prompt
    in Arabic or English with synonym tolerance and typo-resilience.
    """
    if not text:
        return None
    clean = _normalize_chemical_query(text)
    padded = f" {clean} "

    best_match = None
    max_len = 0

    for chem_code, info in CHEMICAL_REGISTRY.items():
        for kw in info["keywords"]:
            norm_kw = _normalize_chemical_query(kw)
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
    """Searches the chemical catalog by keyword query with typo tolerance."""
    if not query:
        return []
    clean = _normalize_chemical_query(query)
    results = []
    for code, info in CHEMICAL_REGISTRY.items():
        score = 0
        if clean in normalize_text(code).lower():
            score += 10
        if clean in normalize_text(info.get("trade_name", "")).lower():
            score += 8
        if clean in normalize_text(info.get("chemical_name", "")).lower():
            score += 8
        if clean in normalize_text(info.get("formula", "")).lower():
            score += 8
        if clean in normalize_text(info.get("cas_number", "")).lower():
            score += 10
        for kw in info.get("keywords", []):
            norm_kw = _normalize_chemical_query(kw)
            if clean in norm_kw or norm_kw in clean:
                score += 6
                break
        if score > 0:
            results.append({"code": code, "score": score, **info})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
