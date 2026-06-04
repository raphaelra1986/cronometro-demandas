# backend/api/schemas.py
"""Schemas Pydantic para validação de dados da API."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DemandCreate(BaseModel):
    """Schema para criar nova demanda."""
    name: str = Field(..., min_length=1, max_length=200)
    card: str = Field(..., min_length=1, max_length=50)
    category: str = Field(default="Extra")


class DemandUpdate(BaseModel):
    """Schema para atualizar demanda."""
    description: Optional[str] = None


class DemandTimeUpdate(BaseModel):
    """Schema para atualizar tempo manualmente."""
    time_seconds: float = Field(..., ge=0)


class DemandResponse(BaseModel):
    """Schema de resposta para demanda."""
    id: int
    name: str
    card: str
    status: str
    accumulated_time: float
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    category: str
    current_elapsed_time: float

    class Config:
        from_attributes = True


class StopDemandRequest(BaseModel):
    """Schema para finalizar demanda."""
    description: str = Field(..., min_length=1)


class ReportRequest(BaseModel):
    """Schema para requisição de relatório."""
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


class ReportItem(BaseModel):
    """Item do relatório."""
    nome: str = Field(..., alias="Nome da Demanda")
    card: str = Field(..., alias="Card")
    tempo: str = Field(..., alias="Tempo Gasto")
    descricao: str = Field(..., alias="Descrição")

    class Config:
        populate_by_name = True


class StatsResponse(BaseModel):
    """Resposta de estatísticas."""
    total_today: str
    total_week: str
    total_month: str
    demands_today: int
    demands_week: int
    avg_time: str
    active_count: int
    category_times: dict


class MessageResponse(BaseModel):
    """Resposta genérica de mensagem."""
    message: str
    success: bool = True
