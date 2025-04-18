from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from src.core.auth.jwt_handler import get_current_user
from src.infra.config.init_database import init_database
from src.infra.adapter.booking_data_repository import BookingDataRepository

router = APIRouter()
logger = logging.getLogger(__name__)


def get_booking_data_repo_by_platform(platform: str) -> BookingDataRepository:
    platform = platform.lower()
    if platform not in ["mmk", "nausys"]:
        raise HTTPException(status_code=400, detail="Platform geçersiz. 'mmk' veya 'nausys' olmalı.")

    db_conf = init_database()
    db_client = db_conf.db_session
    database = db_client["boat_tracker"]
    db_name = f"booking_data_{platform}"
    book_repo = BookingDataRepository(database, db_name)
    return book_repo


def parse_price(price_str: Optional[str]) -> float:
    if not price_str:
        return 0.0
    normalized = price_str.replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return 0.0


@router.get("/prices/compare")
async def compare_prices(
    platform: str = Query(..., description="Platform ismi ('mmk' ya da 'nausys')"),
    date_str: Optional[str] = Query(None, description="Günün tarihi (opsiyonel)"),
    competitor_name: str = Query(..., description="Rakip firma etiketi. Örn: 'rudder'"),
    yacht_id: str = Query(..., description="Rakip firmaya ait teknenin ID'si"),
    yacht_id_sailamor: str = Query(..., description="Sailamor'un (bizim) tekne ID'si"),
    current_user: str = Depends(get_current_user),
):

    booking_repo = get_booking_data_repo_by_platform(platform)
    logger.info(
        "[compare_prices] => competitor=%s, yacht_id=%s, yacht_id_sailamor=%s",
        competitor_name, yacht_id, yacht_id_sailamor
    )

    doc_competitor = await booking_repo.find_booking_doc(
        competitor=competitor_name,
        yacht_id=yacht_id
    )
    if not doc_competitor:
        logger.warning(f"Rakip doc bulunamadı => competitor={competitor_name}, yacht_id={yacht_id}")
        doc_competitor = {}

    doc_sailamor = await booking_repo.find_booking_doc(
        competitor="sailamor",
        yacht_id=yacht_id_sailamor
    )
    if not doc_sailamor:
        logger.warning(f"Sailamor doc bulunamadı => competitor=sailamor, yacht_id={yacht_id_sailamor}")
        doc_sailamor = {}

    competitor_periods = doc_competitor.get("booking_periods", [])
    sailamor_periods = doc_sailamor.get("booking_periods", [])

    competitor_map = {}
    for c_period in competitor_periods:
        pf = c_period.get("period_from")
        pt = c_period.get("period_to")
        details_list = c_period.get("details", [])
        competitor_map[(pf, pt)] = details_list[0] if details_list else None

    sailamor_map = {}
    for s_period in sailamor_periods:
        pf = s_period.get("period_from")
        pt = s_period.get("period_to")
        details_list = s_period.get("details", [])
        sailamor_map[(pf, pt)] = details_list[0] if details_list else None

    all_keys = set(list(competitor_map.keys()) + list(sailamor_map.keys()))
    comparison_list = []
    for (pf, pt) in sorted(all_keys):
        competitor_details = competitor_map.get((pf, pt)) or {}
        sailamor_details   = sailamor_map.get((pf, pt))   or {}

        comparison_list.append({
            "period_from": pf,
            "period_to": pt,
            "competitor_details": competitor_details,
            "sailamor_details": sailamor_details
        })

    result_table = []
    for row in comparison_list:
        pf = row["period_from"]
        pt = row["period_to"]
        comp_det = row["competitor_details"]
        sail_det = row["sailamor_details"]

        # Rakip
        rakip_konum = comp_det.get("port_from", "")
        rakip_fiyat_str = comp_det.get("total_price", "0")
        rakip_list_price_str = comp_det.get("list_price", "0")
        discount_type = comp_det.get("discount_name", "")
        discount_percentage = comp_det.get("discount_percent", "")
        commission_percentage = comp_det.get("commission_percent", "")
        commission_str = comp_det.get("commission", "0")

        rakip_fiyat = parse_price(rakip_fiyat_str)
        rakip_list_price = parse_price(rakip_list_price_str)
        commission = parse_price(commission_str)

        # Biz (Sailamor)
        bizim_konum = sail_det.get("port_from", "")
        bizim_fiyat_str = sail_det.get("total_price", "0")
        bizim_fiyat = parse_price(bizim_fiyat_str)

        # Fark = Bizim Fiyat - Rakip Fiyat (mutlak değer)
        diff = bizim_fiyat - rakip_fiyat
        fark = abs(diff)

        if diff < 0:
            durum = 0
        elif diff > 0:
            durum = 1
        else:
            durum = 2

        tarih_str = f"{pf} - {pt}"
        result_table.append({
            "tarih": tarih_str,
            "bizim_konum": bizim_konum,
            "rakip_konum": rakip_konum,
            "bizim_fiyat": bizim_fiyat,
            "rakip_fiyat": rakip_fiyat,
            "rakip_list_price": rakip_list_price,
            "discount_type": discount_type,
            "discount_percentage": discount_percentage,
            "commission_percentage": commission_percentage,
            "commission": commission,
            "fark": fark,
            "durum": durum
        })

    return result_table
