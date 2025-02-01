from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
import logging
from typing import Dict, Optional, List

from src.infra.adapter.competitor_repository import CompetitorRepository
from src.infra.config.init_database import init_database
from src.core.auth.jwt_handler import get_current_user
from src.api.controllers.bot_controller import BotController
from src.infra.config.config import COMPETITORS
from src.api.dto.bot_dto import BotStatus, BotType

router = APIRouter()
logger = logging.getLogger(__name__)


def get_competitor_repo() -> CompetitorRepository:
    db_conf = init_database()
    db_client = db_conf.db_session
    database = db_client["boat_tracker"]
    return CompetitorRepository(database)


def get_bot_controller(request: Request) -> BotController:
    return request.app.state.bot_controller


class CompetitorCreateRequest(BaseModel):
    competitor_name: str
    search_text: str
    click_text: str


@router.post("/competitor/create-update")
async def create_or_update_competitor(
    req: CompetitorCreateRequest,
    current_user: str = Depends(get_current_user),
    comp_repo: CompetitorRepository = Depends(get_competitor_repo),
    bot_controller: BotController = Depends(get_bot_controller),
):

    logger.info(f"[create_or_update_competitor] Rakip ekleme/güncelleme tetiklendi: {req}")
    bot_instance = bot_controller.bots[BotType.NAUSYS]
    if bot_instance.status != BotStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Nausys bot şu anda çalışmıyor. Lütfen önce /start endpoint'i ile başlatın."
        )

    bot = bot_instance.tracker
    if not bot:
        raise HTTPException(
            status_code=400,
            detail="Bot tracker nesnesi bulunamadı. Muhtemelen bot tam başlatılamadı."
        )

    if not bot.logged_in:
        logger.info("Oturum düşmüş olabilir, tekrar login deneniyor...")
        success = bot.login()
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Nausys bot yeniden login olamadı!"
            )

    try:
        yacht_ids: Dict[str, str] = await bot.scrape_yacht_ids_and_save(
            competitor_name=req.competitor_name,
            company_search_text=req.search_text,
            company_click_text=req.click_text
        )
    except Exception as e:
        logger.error(f"create_or_update_competitor hata: {e}", exc_info=True)
        return {"error": str(e)}

    try:
        await comp_repo.upsert_competitor_info(
            competitor_name=req.competitor_name,
            yacht_ids=yacht_ids,
            search_text=req.search_text,
            click_text=req.click_text
        )
    except Exception as e:
        logger.error(f"upsert_competitor_info hata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Rakip bilgisini kaydederken hata oluştu")

    return {
        "message": "Competitor created/updated successfully",
        "competitor_name": req.competitor_name,
        "yacht_ids": yacht_ids
    }


@router.get("/competitor/yachts/names")
async def get_competitor_yacht_names(
    competitor_name: Optional[str] = Query(
        None, description="Rakip ismi (opsiyonel). Örn 'sailamor'"
    ),
    current_user: str = Depends(get_current_user)
):
    # DB'ye gitmeden, sabit config dosyasında tanımlı COMPETITORS üzerinden çalışıyoruz.
    if competitor_name:
        competitor_doc = COMPETITORS.get(competitor_name)
        if not competitor_doc:
            raise HTTPException(status_code=404, detail=f"{competitor_name} bulunamadı.")
        yacht_ids: Dict[str, str] = competitor_doc.get("yacht_ids", {})
        yachts_list = [{"name": yname, "id": yid} for yname, yid in yacht_ids.items()]
        return {"yachts": yachts_list}
    else:
        result = []
        for comp_name, comp_data in COMPETITORS.items():
            yacht_ids = comp_data.get("yacht_ids", {})
            yachts_list = [{"name": yname, "id": yid} for yname, yid in yacht_ids.items()]
            result.append({
                "competitor_name": comp_name,
                "yachts": yachts_list
            })
        return result


@router.get("/competitor/yachts/details")
async def get_competitor_details(
    competitor_name: Optional[str] = Query(
        None, description="Rakip ismi (opsiyonel)."
    ),
    current_user: str = Depends(get_current_user)
):
    """
    Eğer rakip ismi verilmişse ilgili rakibin dokümanını,
    verilmemişse tüm rakip dokümanlarını döner.
    """
    if competitor_name:
        competitor_doc = COMPETITORS.get(competitor_name)
        if not competitor_doc:
            raise HTTPException(status_code=404, detail=f"{competitor_name} bulunamadı.")
        return competitor_doc
    else:
        return list(COMPETITORS.values())
