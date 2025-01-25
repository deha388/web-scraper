from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import MongoClient
from datetime import datetime
from src.core.auth.jwt_handler import get_current_user
import os

router = APIRouter()

# Örnek MongoDB bağlantısı
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["boat_tracker"]  # sizin veri tabanı adınız


@router.get("/sailamor/yachts/names")
async def get_sailamor_yacht_names(platform: str,
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
    collection_name = f"{platform}_sailamor_{date_collection_format}"

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


@router.get("/sailamor/yachts/periods")
async def get_sailamor_yacht_periods(
        platform: str,
        date_str: str = Query(..., description="YYYY-MM-DD formatında tarih"),
        yacht_name: str = Query(..., description="Tekne ismi"),
        current_user: str = Depends(get_current_user)
):
    """
    Seçilen tarih (YYYY-MM-DD) ve yacht_name'e göre
    `nausys_sailamor_{yyyyMMdd}` koleksiyonundan ilgili teknenin
    period_from / period_to değerlerini (sadece tarih formatında) döndürür.
    """
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Tarih formatı hatalı. YYYY-MM-DD bekleniyor.")

    date_collection_format = selected_date.strftime("%Y%m%d")
    collection_name = f"{platform}_sailamor_{date_collection_format}"

    if collection_name not in db.list_collection_names():
        return {"periods": []}

    coll = db[collection_name]
    documents = list(coll.find({}))

    # Burada seçilen tekneye (yacht_name) ait tüm period_from / period_to çiftlerini toplarız.
    period_list = []
    for doc in documents:
        booking_periods = doc.get("booking_periods", [])
        for bp in booking_periods:
            # "YYYY-MM-DD HH:MM:SS" formatını sadece "YYYY-MM-DD" olarak keselim
            period_from = bp.get("period_from", "")[:10]
            period_to = bp.get("period_to", "")[:10]

            details = bp.get("details", [])
            for detail in details:
                if detail.get("yacht_name") == yacht_name:
                    # Bu booking_period tekneyle eşleşiyor. Period bilgisi ekleyelim
                    period_list.append({
                        "from": period_from,
                        "to": period_to
                    })

    return {"periods": period_list}

@router.get("/sailamor/yachts/details")
async def get_sailamor_details(
    platform: str,
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
    collection_name = f"{platform}_sailamor_{date_collection_format}"

    if collection_name not in db.list_collection_names():
        return {"details": []}

    coll = db[collection_name]
    doc = coll.find_one({
        "booking_periods.period_from": { "$regex": period_from },
        "booking_periods.period_to": { "$regex": period_to },
        "booking_periods.details.yacht_name": yacht_name
    })
    print("result")
    print(doc)
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


@router.get("/sailamor/yachts/all_periods")
def get_all_periods_for_yacht(
        platform: str = Query(..., description="Ör: nausys"),
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
    collection_name = f"{platform}_sailamor_{date_collection_format}"

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