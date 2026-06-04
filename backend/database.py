# database.py
"""Gerenciador de banco de dados com suporte a SQLite e PostgreSQL."""

from __future__ import annotations
import os
import shutil
import glob
from datetime import datetime
from typing import List, Optional, Any, Dict
from logger import log_error, log_info

# Detectar ambiente
DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = DATABASE_URL is not None

if IS_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3

DEFAULT_DB_NAME = "demands.db"
BACKUP_DIR = "backups"
MAX_BACKUPS = 5

# Campos permitidos para update (whitelist de segurança)
ALLOWED_UPDATE_FIELDS = frozenset([
    "name", "card", "status", "accumulated_time",
    "start_time", "end_time", "description", "category"
])


class DatabaseManager:
    """Gerenciador de banco de dados para demandas (SQLite ou PostgreSQL)."""

    def __init__(self, db_name: str = DEFAULT_DB_NAME):
        self.db_name = db_name
        self.is_postgres = IS_POSTGRES
        self._ensure_table()
        log_info(f"Database: {'PostgreSQL' if self.is_postgres else 'SQLite'}")

    def _connect(self):
        """Cria e retorna uma conexão com o banco de dados."""
        if self.is_postgres:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        else:
            conn = sqlite3.connect(
                self.db_name,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row
            return conn

    def _get_cursor(self, conn):
        """Retorna cursor apropriado para o banco."""
        if self.is_postgres:
            return conn.cursor(cursor_factory=RealDictCursor)
        return conn.cursor()

    def _placeholder(self) -> str:
        """Retorna o placeholder correto para o banco."""
        return "%s" if self.is_postgres else "?"

    def _ensure_table(self) -> None:
        """Cria a tabela demands se não existir e adiciona índices."""
        conn = self._connect()
        cur = self._get_cursor(conn)

        if self.is_postgres:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS demands (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    card TEXT NOT NULL,
                    status TEXT NOT NULL,
                    accumulated_time REAL DEFAULT 0.0,
                    start_time TEXT,
                    end_time TEXT,
                    description TEXT,
                    category TEXT DEFAULT 'Extra'
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS demands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    card TEXT NOT NULL,
                    status TEXT NOT NULL,
                    accumulated_time REAL DEFAULT 0.0,
                    start_time TEXT,
                    end_time TEXT,
                    description TEXT,
                    category TEXT DEFAULT 'Extra'
                )
            """)

        conn.commit()

        # Migration: add category column if not exists
        try:
            if self.is_postgres:
                cur.execute("ALTER TABLE demands ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'Extra'")
            else:
                cur.execute("ALTER TABLE demands ADD COLUMN category TEXT DEFAULT 'Extra'")
            conn.commit()
        except Exception:
            conn.rollback()

        # Criar índices
        self._create_indexes(cur)
        conn.commit()
        conn.close()

    def _create_indexes(self, cur) -> None:
        """Cria índices para melhorar performance de queries."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_demands_status ON demands(status)",
            "CREATE INDEX IF NOT EXISTS idx_demands_end_time ON demands(end_time)",
            "CREATE INDEX IF NOT EXISTS idx_demands_category ON demands(category)",
        ]
        for idx_sql in indexes:
            try:
                cur.execute(idx_sql)
            except Exception as e:
                log_error(f"Erro ao criar índice: {e}")

    def _row_to_dict(self, row) -> Optional[Dict]:
        """Converte uma row para dicionário."""
        if row is None:
            return None
        if self.is_postgres:
            return dict(row)
        else:
            return dict(row)

    def insert_demand(self, name: str, card: str, category: str = "Extra") -> int:
        """Insere uma nova demanda no banco."""
        conn = self._connect()
        cur = self._get_cursor(conn)
        ph = self._placeholder()

        if self.is_postgres:
            cur.execute(f"""
                INSERT INTO demands (name, card, status, accumulated_time, category)
                VALUES ({ph}, {ph}, 'pausada', 0.0, {ph})
                RETURNING id
            """, (name, card, category))
            new_id = cur.fetchone()['id']
        else:
            cur.execute(f"""
                INSERT INTO demands (name, card, status, accumulated_time, category)
                VALUES ({ph}, {ph}, 'pausada', 0.0, {ph})
            """, (name, card, category))
            new_id = cur.lastrowid

        conn.commit()
        conn.close()
        return new_id

    def get_all_demands(self) -> List[Dict]:
        """Retorna todas as demandas ordenadas por ID."""
        conn = self._connect()
        cur = self._get_cursor(conn)
        cur.execute("SELECT * FROM demands ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_demand_by_id(self, demand_id: int) -> Optional[Dict]:
        """Retorna uma demanda pelo ID ou None se não existir."""
        conn = self._connect()
        cur = self._get_cursor(conn)
        ph = self._placeholder()
        cur.execute(f"SELECT * FROM demands WHERE id = {ph}", (demand_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_demand(self, demand_id: int, **kwargs: Any) -> bool:
        """Atualiza campos de uma demanda."""
        fields: List[str] = []
        params: List[Any] = []
        ph = self._placeholder()

        for key, value in kwargs.items():
            if key in ALLOWED_UPDATE_FIELDS:
                fields.append(f"{key} = {ph}")
                params.append(value)
            else:
                log_info(f"Campo ignorado em update_demand: {key}")

        if not fields:
            return False

        params.append(demand_id)
        query = f"UPDATE demands SET {', '.join(fields)} WHERE id = {ph}"

        try:
            conn = self._connect()
            cur = self._get_cursor(conn)
            cur.execute(query, params)
            conn.commit()
            affected = cur.rowcount
            conn.close()
            return affected > 0
        except Exception as e:
            log_error(f"Erro ao atualizar demanda {demand_id}: {e}")
            return False

    def delete_demand(self, demand_id: int) -> bool:
        """Remove uma demanda pelo ID."""
        conn = self._connect()
        cur = self._get_cursor(conn)
        ph = self._placeholder()
        cur.execute(f"DELETE FROM demands WHERE id = {ph}", (demand_id,))
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0

    def delete_finalized_demands(self) -> int:
        """Remove todas as demandas finalizadas."""
        conn = self._connect()
        cur = self._get_cursor(conn)
        cur.execute("DELETE FROM demands WHERE status = 'finalizada'")
        conn.commit()
        affected = cur.rowcount
        conn.close()
        log_info(f"Demandas finalizadas removidas: {affected}")
        return affected

    def get_finished_demands_by_period(self, start_iso: str, end_iso: str) -> List[Dict]:
        """Retorna demandas finalizadas em um período."""
        start_ts = f"{start_iso}T00:00:00"
        end_ts = f"{end_iso}T23:59:59"
        conn = self._connect()
        cur = self._get_cursor(conn)
        ph = self._placeholder()
        cur.execute(f"""
            SELECT * FROM demands
            WHERE status = 'finalizada'
            AND end_time BETWEEN {ph} AND {ph}
            ORDER BY end_time
        """, (start_ts, end_ts))
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def create_backup(self) -> Optional[str]:
        """Cria um backup do banco de dados (apenas SQLite)."""
        if self.is_postgres:
            log_info("Backup automático não disponível para PostgreSQL")
            return None

        if not os.path.exists(self.db_name):
            log_info("Backup não criado: banco de dados não existe")
            return None

        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"demands_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        try:
            shutil.copy2(self.db_name, backup_path)
            self._cleanup_old_backups()
            log_info(f"Backup criado: {backup_path}")
            return backup_path
        except OSError as e:
            log_error(f"Erro ao criar backup: {e}")
            return None

    def _cleanup_old_backups(self) -> None:
        """Remove backups antigos."""
        if self.is_postgres:
            return

        pattern = os.path.join(BACKUP_DIR, "demands_backup_*.db")
        backups = sorted(glob.glob(pattern), reverse=True)

        for old_backup in backups[MAX_BACKUPS:]:
            try:
                os.remove(old_backup)
                log_info(f"Backup antigo removido: {old_backup}")
            except OSError as e:
                log_error(f"Erro ao remover backup antigo {old_backup}: {e}")

    def get_available_backups(self) -> List[str]:
        """Retorna lista de arquivos de backup disponíveis."""
        if self.is_postgres or not os.path.exists(BACKUP_DIR):
            return []
        pattern = os.path.join(BACKUP_DIR, "demands_backup_*.db")
        return sorted(glob.glob(pattern), reverse=True)

    def restore_backup(self, backup_path: str) -> bool:
        """Restaura o banco de dados a partir de um arquivo de backup."""
        if self.is_postgres:
            log_error("Restauração de backup não disponível para PostgreSQL")
            return False

        if not os.path.exists(backup_path):
            log_error(f"Backup não encontrado: {backup_path}")
            return False

        try:
            self.create_backup()
            shutil.copy2(backup_path, self.db_name)
            log_info(f"Backup restaurado de: {backup_path}")
            return True
        except OSError as e:
            log_error(f"Erro ao restaurar backup: {e}")
            return False

    def close(self):
        pass
