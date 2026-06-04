# controller.py
from __future__ import annotations
from typing import Dict, List, Optional
from database import DatabaseManager
from model import Demand, Status
from datetime import datetime


class Controller:
    """Controlador principal que orquestra a lógica de negócio."""

    def __init__(self, db_name: Optional[str] = None):
        self.db = DatabaseManager(db_name) if db_name else DatabaseManager()
        self.demands: Dict[int, Demand] = {}
        self.active_demand_id: Optional[int] = None
        self._load_all()

    def _load_all(self) -> None:
        """Carrega todas as demandas do banco para memória."""
        rows = self.db.get_all_demands()
        self.demands = {}
        for r in rows:
            d = Demand.from_db_row(r)
            self.demands[d.id] = d
            if Status.is_em_andamento(d.status):
                self.active_demand_id = d.id

    def add_demand(self, name: str, card: str, category: str = "Extra") -> Demand:
        """Cria uma nova demanda e a adiciona ao banco e cache."""
        new_id = self.db.insert_demand(name, card, category)
        d = Demand(id=new_id, name=name, card=card, status=Status.PAUSADA, accumulated_time=0.0, category=category)
        self.demands[new_id] = d
        return d

    def start_demand(self, demand_id: int) -> bool:
        # pause currently active (if different)
        if self.active_demand_id and self.active_demand_id != demand_id:
            self.pause_demand(self.active_demand_id)

        d = self.demands.get(demand_id)
        if not d:
            return False
        changed = d.start()
        if changed:
            # persist start_time and status
            start_iso = d.start_time.isoformat() if d.start_time else None
            self.db.update_demand(d.id, status=d.status, start_time=start_iso)
            self.active_demand_id = d.id
            return True
        return False

    def pause_demand(self, demand_id: int) -> bool:
        d = self.demands.get(demand_id)
        if not d:
            return False
        changed = d.pause()
        if changed:
            # persist accumulated_time and status, reset start_time in DB
            self.db.update_demand(d.id, accumulated_time=d.accumulated_time, status=d.status, start_time=None)
            if self.active_demand_id == d.id:
                self.active_demand_id = None
            return True
        return False

    def stop_demand(self, demand_id: int, description: str = None) -> bool:
        d = self.demands.get(demand_id)
        if not d:
            return False
        changed = d.stop(description=description)
        if changed:
            end_iso = d.end_time.isoformat() if d.end_time else None
            self.db.update_demand(d.id, accumulated_time=d.accumulated_time, status=d.status, end_time=end_iso, description=d.description)
            if self.active_demand_id == d.id:
                self.active_demand_id = None
            return True
        return False

    def update_demand_description(self, demand_id: int, description: str) -> bool:
        d = self.demands.get(demand_id)
        if not d:
            return False
        d.description = description
        self.db.update_demand(d.id, description=description)
        return True

    # ---- getters / reports ----
    def get_all_demands(self):
        # return list of Demand objects ordered by id
        return [self.demands[k] for k in sorted(self.demands.keys())]

    def get_demand_by_id(self, demand_id: int):
        return self.demands.get(demand_id)

    def get_report_data(self, start_iso_date: str, end_iso_date: str):
        """
        start_iso_date, end_iso_date format: 'YYYY-MM-DD'
        returns list of dicts with keys: 'Nome da Demanda','Card','Tempo Gasto','Descrição'
        """
        rows = self.db.get_finished_demands_by_period(start_iso_date, end_iso_date)
        report = []
        for r in rows:
            d = Demand.from_db_row(r)
            report.append({
                "Nome da Demanda": d.name,
                "Card": d.card,
                "Tempo Gasto": Demand.format_time(d.accumulated_time),
                "Descrição": d.description or ""
            })
        return report

    def delete_demand(self, demand_id: int) -> bool:
        """Delete a single demand by ID."""
        if demand_id not in self.demands:
            return False
        success = self.db.delete_demand(demand_id)
        if success:
            del self.demands[demand_id]
            if self.active_demand_id == demand_id:
                self.active_demand_id = None
        return success

    def update_demand_time(self, demand_id: int, new_time_seconds: float) -> bool:
        """Update the accumulated time of a demand manually."""
        d = self.demands.get(demand_id)
        if not d:
            return False
        d.accumulated_time = max(0.0, new_time_seconds)
        self.db.update_demand(d.id, accumulated_time=d.accumulated_time)
        return True

    def limpar_finalizadas(self) -> None:
        """Remove todas as demandas finalizadas do banco e da memória."""
        self.db.delete_finalized_demands()
        # Remove from in-memory cache
        ids_to_remove = [d.id for d in self.demands.values() if Status.is_finalizada(d.status)]
        for demand_id in ids_to_remove:
            del self.demands[demand_id]

    def close(self):
        self.db.close()
