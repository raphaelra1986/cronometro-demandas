# model.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, Any


# Constantes de tempo
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600


class Status:
    """Status constants for demands."""
    PAUSADA = "pausada"
    EM_ANDAMENTO = "em_andamento"
    FINALIZADA = "finalizada"

    # Mapeamento de aliases para status normalizado
    _ALIASES = {
        # Pausada
        "pausada": PAUSADA,
        "paused": PAUSADA,
        # Em andamento
        "em_andamento": EM_ANDAMENTO,
        "em andamento": EM_ANDAMENTO,
        "in_progress": EM_ANDAMENTO,
        # Finalizada
        "finalizada": FINALIZADA,
        "finalized": FINALIZADA,
    }

    @classmethod
    def normalize(cls, status: Optional[str]) -> str:
        """Normaliza qualquer formato de status para o padrão."""
        if status is None:
            return cls.PAUSADA
        status_lower = str(status).lower().strip()
        return cls._ALIASES.get(status_lower, cls.PAUSADA)

    @classmethod
    def is_em_andamento(cls, status: Optional[str]) -> bool:
        """Verifica se o status é 'em andamento'."""
        return cls.normalize(status) == cls.EM_ANDAMENTO

    @classmethod
    def is_pausada(cls, status: Optional[str]) -> bool:
        """Verifica se o status é 'pausada'."""
        return cls.normalize(status) == cls.PAUSADA

    @classmethod
    def is_finalizada(cls, status: Optional[str]) -> bool:
        """Verifica se o status é 'finalizada'."""
        return cls.normalize(status) == cls.FINALIZADA


class Categories:
    """Available categories for demands."""
    SPRINT = "Sprint"
    FURACAO = "Furacão"
    META = "Meta"
    EXTRA = "Extra"

    @classmethod
    def all(cls):
        return [cls.SPRINT, cls.FURACAO, cls.META, cls.EXTRA]


class Demand:
    """
    Model for a demand/task with timer control.
    """

    def __init__(
        self,
        id: int,
        name: str,
        card: str,
        status: str = Status.PAUSADA,
        accumulated_time: float = 0.0,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
        description: Optional[str] = None,
        category: str = Categories.EXTRA
    ):
        self.id = id
        self.name = name
        self.card = card
        self.status = status  # Status.PAUSADA, Status.EM_ANDAMENTO, Status.FINALIZADA
        self.accumulated_time = float(accumulated_time or 0.0)
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.description = description
        self.category = category or Categories.EXTRA

    # --- helpers for robust parsing (accepts ISO strings or numeric timestamps)
    def _parse_time(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        # if numeric-like string or number: treat as float seconds since epoch
        try:
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(float(value))
            v = str(value)
            # try ISO first
            try:
                return datetime.fromisoformat(v)
            except Exception:
                # fallback: if numeric string
                try:
                    return datetime.fromtimestamp(float(v))
                except Exception:
                    return None
        except Exception:
            return None

    # --- timer control (in-memory only; DB write handled by Controller) ---
    def start(self) -> bool:
        """Inicia o cronômetro se estiver pausado."""
        if Status.is_pausada(self.status):
            self.start_time = datetime.now()
            self.status = Status.EM_ANDAMENTO
            return True
        return False

    def pause(self) -> bool:
        """Pausa o cronômetro se estiver em andamento."""
        if Status.is_em_andamento(self.status) and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.accumulated_time += elapsed
            self.start_time = None
            self.status = Status.PAUSADA
            return True
        return False

    def stop(self, description: Optional[str] = None) -> bool:
        """Finaliza a demanda, acumulando tempo restante se em andamento."""
        if Status.is_em_andamento(self.status) and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.accumulated_time += elapsed
        self.start_time = None
        self.end_time = datetime.now()
        self.status = Status.FINALIZADA
        if description is not None:
            self.description = description
        return True

    def get_current_elapsed_time(self) -> float:
        """Retorna o tempo total decorrido incluindo tempo atual se em andamento."""
        if Status.is_em_andamento(self.status) and self.start_time:
            return self.accumulated_time + (datetime.now() - self.start_time).total_seconds()
        return self.accumulated_time

    @staticmethod
    def format_time(total_seconds: float) -> str:
        """Formata segundos em string HHh MMm SSs."""
        total_seconds = int(total_seconds or 0)
        hours = total_seconds // SECONDS_PER_HOUR
        minutes = (total_seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE
        seconds = total_seconds % SECONDS_PER_MINUTE
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    # helper to create Demand from DB row (sqlite3.Row or sequence)
    @classmethod
    def from_db_row(cls, row):
        # row can be sqlite3.Row (mapping) or tuple
        if hasattr(row, "keys"):
            id = row["id"]
            name = row["name"]
            card = row["card"]
            status = row["status"]
            accumulated_time = row["accumulated_time"]
            start_time = row["start_time"]
            end_time = row["end_time"]
            description = row["description"]
            category = row["category"] if "category" in row.keys() else Categories.EXTRA
        else:
            # Tuple format: (id, name, card, status, accumulated_time, start_time, end_time, description, category)
            if len(row) >= 9:
                id, name, card, status, accumulated_time, start_time, end_time, description, category = row[:9]
            else:
                id, name, card, status, accumulated_time, start_time, end_time, description = row[:8]
                category = Categories.EXTRA
        return cls(
            id=id,
            name=name,
            card=card,
            status=status,
            accumulated_time=accumulated_time,
            start_time=start_time,
            end_time=end_time,
            description=description,
            category=category
        )
