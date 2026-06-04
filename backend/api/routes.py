# backend/api/routes.py
"""Rotas REST da API."""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime, timedelta

from controller import Controller
from model import Status, Categories, Demand
from .schemas import (
    DemandCreate,
    DemandResponse,
    DemandTimeUpdate,
    StopDemandRequest,
    StatsResponse,
    MessageResponse,
    ReportItem,
)

router = APIRouter(prefix="/api", tags=["demands"])

# Controller global (será injetado pelo main.py)
controller: Controller = None


def set_controller(ctrl: Controller) -> None:
    """Define o controller global."""
    global controller
    controller = ctrl


def demand_to_response(d: Demand) -> DemandResponse:
    """Converte Demand para DemandResponse."""
    return DemandResponse(
        id=d.id,
        name=d.name,
        card=d.card,
        status=d.status,
        accumulated_time=d.accumulated_time,
        start_time=d.start_time.isoformat() if d.start_time else None,
        end_time=d.end_time.isoformat() if d.end_time else None,
        description=d.description,
        category=getattr(d, 'category', Categories.EXTRA) or Categories.EXTRA,
        current_elapsed_time=d.get_current_elapsed_time(),
    )


@router.get("/demands", response_model=List[DemandResponse])
async def list_demands():
    """Lista todas as demandas."""
    demands = controller.get_all_demands()
    return [demand_to_response(d) for d in demands]


@router.post("/demands", response_model=DemandResponse)
async def create_demand(data: DemandCreate):
    """Cria uma nova demanda."""
    # Validar categoria
    category = data.category if data.category in Categories.all() else Categories.EXTRA
    demand = controller.add_demand(data.name, data.card, category)
    return demand_to_response(demand)


@router.get("/demands/{demand_id}", response_model=DemandResponse)
async def get_demand(demand_id: int):
    """Obtém uma demanda por ID."""
    demand = controller.get_demand_by_id(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")
    return demand_to_response(demand)


@router.delete("/demands/{demand_id}", response_model=MessageResponse)
async def delete_demand(demand_id: int):
    """Remove uma demanda."""
    demand = controller.get_demand_by_id(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")

    success = controller.delete_demand(demand_id)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao remover demanda")

    return MessageResponse(message="Demanda removida com sucesso")


@router.post("/demands/{demand_id}/start", response_model=DemandResponse)
async def start_demand(demand_id: int):
    """Inicia o cronômetro de uma demanda."""
    demand = controller.get_demand_by_id(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")

    success = controller.start_demand(demand_id)
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível iniciar a demanda")

    return demand_to_response(controller.get_demand_by_id(demand_id))


@router.post("/demands/{demand_id}/pause", response_model=DemandResponse)
async def pause_demand(demand_id: int):
    """Pausa o cronômetro de uma demanda."""
    demand = controller.get_demand_by_id(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")

    success = controller.pause_demand(demand_id)
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível pausar a demanda")

    return demand_to_response(controller.get_demand_by_id(demand_id))


@router.post("/demands/{demand_id}/stop", response_model=DemandResponse)
async def stop_demand(demand_id: int, data: StopDemandRequest):
    """Finaliza uma demanda."""
    demand = controller.get_demand_by_id(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")

    success = controller.stop_demand(demand_id, data.description)
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível finalizar a demanda")

    return demand_to_response(controller.get_demand_by_id(demand_id))


@router.patch("/demands/{demand_id}/time", response_model=DemandResponse)
async def update_demand_time(demand_id: int, data: DemandTimeUpdate):
    """Atualiza o tempo de uma demanda manualmente."""
    demand = controller.get_demand_by_id(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")

    success = controller.update_demand_time(demand_id, data.time_seconds)
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível atualizar o tempo")

    return demand_to_response(controller.get_demand_by_id(demand_id))


@router.patch("/demands/{demand_id}/description", response_model=DemandResponse)
async def update_demand_description(demand_id: int, description: str = Query(...)):
    """Atualiza a descrição de uma demanda."""
    demand = controller.get_demand_by_id(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")

    success = controller.update_demand_description(demand_id, description)
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível atualizar a descrição")

    return demand_to_response(controller.get_demand_by_id(demand_id))


@router.delete("/demands/finalized/clear", response_model=MessageResponse)
async def clear_finalized_demands():
    """Remove todas as demandas finalizadas."""
    controller.limpar_finalizadas()
    return MessageResponse(message="Demandas finalizadas removidas")


@router.get("/reports")
async def get_report(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
):
    """Gera relatório de demandas finalizadas no período."""
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")

    rows = controller.get_report_data(start_date, end_date)
    return rows


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Retorna estatísticas das demandas."""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    all_demands = controller.get_all_demands()

    total_today = 0.0
    total_week = 0.0
    total_month = 0.0
    demands_today = 0
    demands_week = 0
    active_count = 0
    finalized_times = []
    category_times = {cat: 0.0 for cat in Categories.all()}

    for d in all_demands:
        elapsed = d.get_current_elapsed_time()

        # Demandas ativas
        if Status.is_em_andamento(d.status) or Status.is_pausada(d.status):
            active_count += 1
            total_today += elapsed
            total_week += elapsed
            total_month += elapsed

        # Demandas finalizadas
        if Status.is_finalizada(d.status) and d.end_time:
            finalized_times.append(d.accumulated_time)

            if d.end_time >= today_start:
                demands_today += 1
                total_today += d.accumulated_time
            if d.end_time >= week_start:
                demands_week += 1
                total_week += d.accumulated_time
            if d.end_time >= month_start:
                total_month += d.accumulated_time

        # Tempo por categoria
        cat = getattr(d, 'category', Categories.EXTRA) or Categories.EXTRA
        if cat not in category_times:
            cat = Categories.EXTRA
        category_times[cat] += elapsed

    avg_time = sum(finalized_times) / len(finalized_times) if finalized_times else 0

    return StatsResponse(
        total_today=Demand.format_time(total_today),
        total_week=Demand.format_time(total_week),
        total_month=Demand.format_time(total_month),
        demands_today=demands_today,
        demands_week=demands_week,
        avg_time=Demand.format_time(avg_time),
        active_count=active_count,
        category_times={k: Demand.format_time(v) for k, v in category_times.items()},
    )


@router.get("/categories")
async def get_categories():
    """Retorna lista de categorias disponíveis."""
    return Categories.all()
