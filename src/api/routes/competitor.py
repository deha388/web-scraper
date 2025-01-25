# competitor.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from pymongo import MongoClient
import os
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import logging
import asyncio
from src.core.auth.jwt_handler import get_current_user
from src.core.tracker.nausys_tracker import NausysTracker

router = APIRouter()

logger = logging.getLogger(__name__)


class CompetitorCreateRequest(BaseModel):
    competitor_name: str
    search_text: str
    click_text: str


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["boat_tracker"]  # kendi DB adınız


class CompetitorCreateRequest(BaseModel):
    competitor_name: str
    search_text: str
    click_text: str


@router.post("/create-update")
async def create_or_update_competitor(
        req: CompetitorCreateRequest,
        current_user: str = Depends(get_current_user),
):
    """
    Rakip ekleme/güncelleme endpointi:
    - Selenium ile firmayı filtreler
    - Yat ID'lerini bulur
    - DB'ye kaydeder (search_text, click_text, yacht_ids).
    """
    logger.info(f"Rakip ekleme/güncelleme tetiklendi: {req}")

    bot = NausysTracker()
    bot.setup_driver()
    try:
        yacht_ids = await bot.scrape_yacht_ids_and_save(
            competitor_name=req.competitor_name,
            company_search_text=req.search_text,
            company_click_text=req.click_text
        )
        return {
            "message": "Competitor created/updated successfully",
            "competitor_name": req.competitor_name,
            "yacht_ids": yacht_ids
        }
    except Exception as e:
        logger.error(f"create_or_update_competitor hata: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        await asyncio.sleep(2)
        if bot.driver:
            bot.driver.quit()


@router.get("/competitor/period-yachts")
def get_competitor_period_yachts(
        platform: str,
        date_str: str = Query(..., description="YYYY-MM-DD formatında"),
        competitor: str = Query(..., description="Ör: rudder_moor, sailtime, navigo"),
        period_from: str = Query(..., description="Tam datetime: 2025-04-12 17:00:00"),
        period_to: str = Query(..., description="Tam datetime: 2025-04-19 08:00:00"),
        current_user: str = Depends(get_current_user)
):
    """
    nausys_{competitor}_{YYYYMMDD} koleksiyonunda,
    period_from / period_to alanlarıyla eşleşen booking_periods içindeki
    yacht_name değerlerini (distinct) döndürür.
    """

    # 1) date_str'i parse edip koleksiyon adı oluştur
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Tarih formatı hatalı.")

    date_collection_format = selected_date.strftime("%Y%m%d")  # "20250119" vb.
    collection_name = f"{platform}_{competitor}_{date_collection_format}"

    if collection_name not in db.list_collection_names():
        return {"yacht_names": []}  # veya 404

    coll = db[collection_name]
    documents = list(coll.find({}))

    yacht_name_set = set()

    for doc in documents:
        booking_periods = doc.get("booking_periods", [])
        for bp in booking_periods:
            pf = bp.get("period_from", "")
            pt = bp.get("period_to", "")
            # Ör: "2025-04-12 17:00:00"

            # Tam eşleşme istiyorsak:
            if period_from in pf and period_to in pt:
                # Eşleşen booking_period
                details = bp.get("details", [])
                for detail in details:
                    yname = detail.get("yacht_name")
                    if yname:
                        yacht_name_set.add(yname)

    return {"yacht_names": list(yacht_name_set)}


@router.get("/competitor/yachts/details")
async def get_competitor_details(
        platform: str,
        competitor: str,
        date_str: str,
        yacht_name: str,
        period_from: str,
        period_to: str,
        current_user: str = Depends(get_current_user)
):
    """
    nausys_{sailamor}_{YYYYMMDD} koleksiyonundan,
    istenen (yacht_name, period_from, period_to) eşleşen kaydın "details" alanını döndürür.
    """
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Tarih formatı geçersiz")

    date_collection_format = selected_date.strftime("%Y%m%d")  # örn. "20250119"
    collection_name = f"{platform}_{competitor}_{date_collection_format}"

    if collection_name not in db.list_collection_names():
        return {"details": []}

    coll = db[collection_name]
    doc = coll.find_one({
        "booking_periods.period_from": {"$regex": period_from},
        "booking_periods.period_to": {"$regex": period_to},
        "booking_periods.details.yacht_name": yacht_name
    })

    if not doc:
        return {"details": []}

    # İlgili booking_period'ı bulup, o period içindeki "details" listesini döndürelim
    # Bir dokümanda birden fazla booking_period olabilir. Uygun olanı bulup oradaki details'i alalım.
    details_list = []
    for bp in doc.get("booking_periods", []):
        if period_from in bp.get("period_from") and period_to in bp.get("period_to"):
            for d in bp.get("details", []):
                if d.get("yacht_name") == yacht_name:
                    details_list.append(d)
    return {"details": details_list}


@router.get("/competitor/yachts/all_periods")
def get_all_periods_for_yacht(
        platform: str = Query(..., description="Ör: nausys"),
        competitor: str = Query(..., description="Ör: ruud_more"),
        date_str: str = Query(..., description="YYYY-MM-DD formatında tarih"),
        yacht_name: str = Query(..., description="Tekne ismi"),
        current_user: str = Depends(get_current_user)
):
    # 1) Tarihi parse et
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Tarih formatı geçersiz (YYYY-MM-DD).")

    date_collection_format = selected_date.strftime("%Y%m%d")  # Örnek: "20250412"
    collection_name = f"{platform}_{competitor}_{date_collection_format}"

    # 2) Koleksiyon var mı?
    if collection_name not in db.list_collection_names():
        return {"periods": []}

    coll = db[collection_name]

    # 3) Tekne adına göre filtreleme
    #    Bazı yapılarda 'yacht_name' toplu aranır, "booking_periods.details.yacht_name" => match
    #    En basit yöntem => Tüm dokümanları al, python tarafında filtrele.
    documents = list(coll.find({}))

    result_periods = []

    # 4) booking_periods içindeki her period,
    #    details içinde "yacht_name" = aranan tekne ise o periodu listeye ekle.
    for doc in documents:
        booking_periods = doc.get("booking_periods", [])
        for bp in booking_periods:
            pf = bp.get("period_from", "")
            pt = bp.get("period_to", "")
            details_list = bp.get("details", [])
            for detail in details_list:
                if detail.get("yacht_name") == yacht_name:
                    # location / fiyat gibi bilgileri alalım
                    location = detail.get("location", "")
                    prices = detail.get("prices", {})
                    discounted_price = prices.get("discounted_price", "")
                    original_price = prices.get("original_price", "")
                    # vs. ek alanlar

                    # Listemize ekleyelim
                    result_periods.append({
                        "period_from": pf[:10],
                        "period_to": pt[:10],
                        "location": location,
                        "discounted_price": discounted_price,
                        "original_price": original_price
                        # vs. eklenecek alanlar
                    })

    return {"periods": result_periods}


@router.get("/competitor/yachts/names")
async def get_competitor_yacht_names(platform: str, competitor: str,
                                     date_str: str = Query(..., description="YYYY-MM-DD formatında tarih"),
                                     current_user: str = Depends(get_current_user)):
    """
    Seçilen tarihe göre `nausys_sailamor_{yyyyMMdd}` koleksiyonundan
    TÜM `yacht_name` değerlerini (distinct) döndürür.
    """
    # 1) Tarihi parse et ve koleksiyon adını oluştur
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Tarih formatı hatalı. YYYY-MM-DD bekleniyor.")

    date_collection_format = selected_date.strftime("%Y%m%d")  # Örneğin "20250119"
    collection_name = f"{platform}_{competitor}_{date_collection_format}"

    # 2) Koleksiyon var mı?
    if collection_name not in db.list_collection_names():
        # Dilerseniz 404 veya boş liste döndürebilirsiniz
        return {"yacht_names": []}

    coll = db[collection_name]
    documents = list(coll.find({}))

    # 3) Distinct yacht_name'leri toplamak için bir set kullanalım
    yacht_name_set = set()

    for doc in documents:
        booking_periods = doc.get("booking_periods", [])
        for bp in booking_periods:
            details = bp.get("details", [])
            for detail in details:
                yacht_name = detail.get("yacht_name")
                if yacht_name:
                    yacht_name_set.add(yacht_name)

    # 4) JSON formatında döndürmek için sete -> listeye çevir
    return {"yacht_names": list(yacht_name_set)}
