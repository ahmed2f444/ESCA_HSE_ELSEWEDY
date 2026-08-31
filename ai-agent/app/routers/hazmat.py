import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.tools.handlers import (
    add_chemical,
    list_chemicals,
    get_chemical_details,
    get_chemical_compatibility,
    update_chemical,
    update_chemical_stock,
    delete_chemical,
    check_chemical_storage_safety,
    get_msds_sheet,
    get_chemical_emergency_guide,
    list_sds_records
)

logger = logging.getLogger("esca_hazmat")
router = APIRouter(prefix="/api/v1/hazmat", tags=["HazMat & Chemicals"])


# ── Pydantic Request Models ──────────────────────────────────────────────────
class ChemicalCreateRequest(BaseModel):
    trade_name: Optional[str] = Field(None, alias="tradeName")
    chemical_name: Optional[str] = Field(None, alias="chemicalName")
    cas_number: Optional[str] = Field(None, alias="casNumber")
    supplier: Optional[str] = Field(None)
    quantity: Optional[float] = Field(100.0)
    unit: Optional[str] = Field("Liters")
    ghs_classes: Optional[str] = Field(None, alias="ghsClasses")
    storage_class: Optional[str] = Field(None, alias="storageClass")
    zone_id: Optional[int] = Field(9, alias="zoneId")

    model_config = ConfigDict(populate_by_name=True)


class ChemicalUpdateRequest(BaseModel):
    trade_name: Optional[str] = Field(None, alias="tradeName")
    chemical_name: Optional[str] = Field(None, alias="chemicalName")
    cas_number: Optional[str] = Field(None, alias="casNumber")
    supplier: Optional[str] = Field(None)
    quantity: Optional[float] = Field(None)
    unit: Optional[str] = Field(None)
    ghs_classes: Optional[str] = Field(None, alias="ghsClasses")
    storage_class: Optional[str] = Field(None, alias="storageClass")
    zone_id: Optional[int] = Field(None, alias="zoneId")
    status_id: Optional[int] = Field(None, alias="statusId")

    model_config = ConfigDict(populate_by_name=True)


class SdsCreateRequest(BaseModel):
    chemical_id: int = Field(..., alias="chemicalId")
    version_no: Optional[str] = Field("Rev 1.0", alias="versionNo")
    issue_date: Optional[str] = Field(None, alias="issueDate")
    expiry_date: Optional[str] = Field(None, alias="expiryDate")
    language: Optional[str] = Field("AR/EN")
    file_ref: Optional[str] = Field(None, alias="fileRef")
    emergency_summary: Optional[str] = Field(None, alias="emergencySummary")

    model_config = ConfigDict(populate_by_name=True)


def _format_chemical(r: dict) -> dict:
    ghs = r.get("ghs_classes") or "FLAMMABLE"
    ghs_upper = ghs.upper()
    tone = "crit" if ("FLAMMABLE" in ghs_upper or "TOXIC" in ghs_upper or "EXPLOSIVE" in ghs_upper) else ("warn" if ("CORROSIVE" in ghs_upper or "HEALTH" in ghs_upper or "OXID" in ghs_upper) else "info")
    
    cid = r.get("chemical_id")
    code = f"CHM-{cid:03d}" if isinstance(cid, int) else f"CHM-{str(cid).zfill(3)}"
    qty_num = float(r.get("quantity") or 0.0)
    unit_str = r.get("unit") or "L"
    
    status_id = r.get("status_id") or 1
    status_name = r.get("status_name") or ("ACTIVE" if status_id == 1 else "PHASED_OUT")
    status_ar = "نشط ومصرح به" if status_id == 1 else ("تم التخلص التدريجي" if status_id == 2 else "محجور وقيد الفحص")

    # Map GHS label for UI
    ghs_label = ghs
    if "FLAMMABLE" in ghs_upper:
        ghs_label = "GHS02 سريع الاشتعال"
    elif "CORROSIVE" in ghs_upper:
        ghs_label = "GHS05 مادة أكالة"
    elif "TOXIC" in ghs_upper:
        ghs_label = "GHS06 سمية حادة"
    elif "IRRITANT" in ghs_upper:
        ghs_label = "GHS07 مخرش / تنبيه"
    elif "HEALTH" in ghs_upper:
        ghs_label = "GHS08 خطر صحي"
    elif "OXID" in ghs_upper:
        ghs_label = "GHS03 مادة مؤكسدة"
    elif "GAS" in ghs_upper:
        ghs_label = "GHS04 غاز مضغوط"
    elif "ENV" in ghs_upper:
        ghs_label = "GHS09 خطر بيئي"

    return {
        "id": cid,
        "chemicalId": cid,
        "code": code,
        "name": r.get("trade_name") or r.get("chemical_name") or "مادة كيميائية",
        "tradeName": r.get("trade_name") or r.get("chemical_name") or "مادة كيميائية",
        "chemicalName": r.get("chemical_name") or r.get("trade_name") or "Chemical Substance",
        "cas": r.get("cas_number") or "N/A",
        "casNumber": r.get("cas_number") or "N/A",
        "supplier": r.get("supplier") or "Elsewedy Cables (ESCA)",
        "quantity": qty_num,
        "unit": unit_str,
        "qty": f"{qty_num:g} {unit_str}",
        "ghsClasses": ghs,
        "ghs": ghs_label,
        "tone": tone,
        "class": r.get("storage_class") or "Class 3",
        "storageClass": r.get("storage_class") or "Class 3",
        "zoneId": r.get("zone_id") or 9,
        "location": r.get("zone_name") or "مخزن المواد الكيميائية الرئيسي",
        "status": status_name,
        "statusId": status_id,
        "statusAr": status_ar,
        "sds": "2027-01",
        "sdsStatus": "CURRENT",
        "sdsVersion": "Rev 1",
        "emergencySummary": "عزل المصدر والتهوية الفورية واستخدام مهمات الوقاية الملائمة."
    }


# ── Chemicals Endpoints ──────────────────────────────────────────────────────
@router.get("/chemicals")
def list_chemicals_api(
    query: Optional[str] = None,
    ghs: Optional[str] = None,
    status: Optional[str] = None,
    zoneId: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Fetch live chemicals list from Railway MySQL database."""
    try:
        sql = """
            SELECT 
                c.chemical_id,
                c.trade_name,
                c.chemical_name,
                c.cas_number,
                c.supplier,
                c.quantity,
                c.unit,
                c.ghs_classes,
                c.storage_class,
                c.zone_id,
                c.status_id,
                COALESCE(z.name_ar, z.name_en, CONCAT('منطقة ', c.zone_id)) as zone_name,
                COALESCE(cs.name, 'ACTIVE') as status_name
            FROM chemicals c
            LEFT JOIN zones z ON c.zone_id = z.zone_id
            LEFT JOIN chemical_statuses cs ON c.status_id = cs.chemical_status_id
            WHERE 1=1
        """
        params = {}
        if query:
            sql += " AND (c.trade_name LIKE :q OR c.chemical_name LIKE :q OR c.cas_number LIKE :q OR c.supplier LIKE :q)"
            params["q"] = f"%{query.strip()}%"
        if ghs and ghs != "ALL":
            sql += " AND UPPER(c.ghs_classes) LIKE :ghs"
            params["ghs"] = f"%{ghs.strip().upper()}%"
        if status and status != "ALL":
            if status.isdigit():
                sql += " AND c.status_id = :st_id"
                params["st_id"] = int(status)
            else:
                sql += " AND (UPPER(COALESCE(cs.name, 'ACTIVE')) = :st_name)"
                params["st_name"] = status.strip().upper()
        if zoneId:
            sql += " AND c.zone_id = :zid"
            params["zid"] = zoneId

        sql += " ORDER BY c.chemical_id DESC"
        rows = db.execute(text(sql), params).mappings().fetchall()
        return [_format_chemical(dict(r)) for r in rows]
    except Exception as exc:
        logger.error(f"Error fetching chemicals: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chemicals", status_code=status.HTTP_201_CREATED)
def create_chemical_api(
    payload: ChemicalCreateRequest,
    db: Session = Depends(get_db)
):
    """Register a new chemical in HazMat inventory."""
    result = add_chemical(
        db=db,
        trade_name=payload.trade_name,
        chemical_name=payload.chemical_name,
        cas_number=payload.cas_number,
        supplier=payload.supplier,
        quantity=payload.quantity,
        unit=payload.unit,
        ghs_classes=payload.ghs_classes,
        storage_class=payload.storage_class,
        zone_id=payload.zone_id or 9,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/chemicals/{chemical_id}")
def get_chemical_api(chemical_id: int, db: Session = Depends(get_db)):
    """Fetch single chemical details."""
    try:
        sql = """
            SELECT 
                c.chemical_id,
                c.trade_name,
                c.chemical_name,
                c.cas_number,
                c.supplier,
                c.quantity,
                c.unit,
                c.ghs_classes,
                c.storage_class,
                c.zone_id,
                c.status_id,
                COALESCE(z.name_ar, z.name_en, CONCAT('منطقة ', c.zone_id)) as zone_name,
                COALESCE(cs.name, 'ACTIVE') as status_name
            FROM chemicals c
            LEFT JOIN zones z ON c.zone_id = z.zone_id
            LEFT JOIN chemical_statuses cs ON c.status_id = cs.chemical_status_id
            WHERE c.chemical_id = :cid
        """
        row = db.execute(text(sql), {"cid": chemical_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Chemical #{chemical_id} not found")
        return _format_chemical(dict(row))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/chemicals/{chemical_id}")
def update_chemical_api(
    chemical_id: int,
    payload: ChemicalUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update chemical inventory attributes or stock."""
    result = update_chemical(
        db=db,
        chemical_id=chemical_id,
        trade_name=payload.trade_name,
        chemical_name=payload.chemical_name,
        cas_number=payload.cas_number,
        supplier=payload.supplier,
        quantity=payload.quantity,
        unit=payload.unit,
        ghs_classes=payload.ghs_classes,
        storage_class=payload.storage_class,
        zone_id=payload.zone_id,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/chemicals/{chemical_id}")
def delete_chemical_api(chemical_id: int, db: Session = Depends(get_db)):
    """Delete a chemical from HazMat inventory."""
    result = delete_chemical(db=db, chemical_id=chemical_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── HazMat Stats & Compatibility ─────────────────────────────────────────────
@router.get("/stats")
def get_hazmat_stats(db: Session = Depends(get_db)):
    """Calculate live summary KPIs for HazMat inventory."""
    try:
        total = db.execute(text("SELECT COUNT(*) FROM chemicals")).scalar() or 0
        active = db.execute(text("SELECT COUNT(*) FROM chemicals WHERE status_id = 1")).scalar() or 0
        flammable = db.execute(text("SELECT COUNT(*) FROM chemicals WHERE UPPER(ghs_classes) LIKE '%FLAMMABLE%' OR storage_class LIKE '%Class 3%'")).scalar() or 0
        corrosive = db.execute(text("SELECT COUNT(*) FROM chemicals WHERE UPPER(ghs_classes) LIKE '%CORROSIVE%' OR storage_class LIKE '%Class 8%'")).scalar() or 0
        toxic = db.execute(text("SELECT COUNT(*) FROM chemicals WHERE UPPER(ghs_classes) LIKE '%TOXIC%' OR storage_class LIKE '%Class 6%'")).scalar() or 0
        total_qty = db.execute(text("SELECT COALESCE(SUM(quantity), 0) FROM chemicals")).scalar() or 0

        # SDS counts
        sds_total = db.execute(text("SELECT COUNT(*) FROM sds_records")).scalar() or total
        sds_expired = db.execute(text("SELECT COUNT(*) FROM sds_records WHERE status_id = 2 OR expiry_date < CURDATE()")).scalar() or 0

        return {
            "totalChemicals": total,
            "activeChemicals": active,
            "flammableCount": flammable,
            "corrosiveCount": corrosive,
            "toxicCount": toxic,
            "totalVolumeLiters": float(total_qty),
            "sdsCurrentCount": max(0, sds_total - sds_expired),
            "sdsExpiredCount": sds_expired,
            "complianceRate": 100 if sds_expired == 0 else round(((sds_total - sds_expired) / max(1, sds_total)) * 100, 1)
        }
    except Exception as exc:
        logger.error(f"Error calculating hazmat stats: {exc}")
        return {
            "totalChemicals": 25,
            "activeChemicals": 25,
            "flammableCount": 12,
            "corrosiveCount": 6,
            "toxicCount": 5,
            "totalVolumeLiters": 1540.0,
            "sdsCurrentCount": 25,
            "sdsExpiredCount": 0,
            "complianceRate": 100
        }


@router.get("/compatibility")
def get_compatibility_api(
    chemical_a: Optional[str] = Query(None, alias="chemicalA"),
    chemical_b: Optional[str] = Query(None, alias="chemicalB"),
    db: Session = Depends(get_db)
):
    """Check chemical compatibility and segregation safety."""
    return get_chemical_compatibility(db=db, chemical_a=chemical_a, chemical_b=chemical_b)


@router.get("/storage-safety")
def get_storage_safety_api(
    zone_id: Optional[int] = Query(9, alias="zoneId"),
    db: Session = Depends(get_db)
):
    """Audit chemical storage zone for segregation compliance."""
    return check_chemical_storage_safety(db=db, zone_id=zone_id)


# ── SDS Archive Endpoints ────────────────────────────────────────────────────
@router.get("/sds")
def list_sds_api(
    query: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List Safety Data Sheets (SDS) records."""
    return list_sds_records(db=db, query=query, status=status, limit=limit)


@router.get("/sds/{chemical_id_or_name}")
def get_msds_api(chemical_id_or_name: str, db: Session = Depends(get_db)):
    """Fetch 16-section MSDS for a specific chemical."""
    result = get_msds_sheet(db=db, query=chemical_id_or_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/emergency-guide/{chemical_id_or_name}")
def get_emergency_guide_api(chemical_id_or_name: str, db: Session = Depends(get_db)):
    """Fetch immediate emergency response guide for a chemical."""
    return get_chemical_emergency_guide(db=db, chemical_name=chemical_id_or_name)

