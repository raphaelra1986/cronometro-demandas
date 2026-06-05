# backend/integrations/teams.py
"""Integração com Microsoft Teams via Webhook."""

from __future__ import annotations
import os
import httpx
from typing import Optional
from logger import log_info, log_error

# URL do Webhook do Teams (configurar via variável de ambiente)
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")


def is_teams_enabled() -> bool:
    """Verifica se a integração com Teams está habilitada."""
    return TEAMS_WEBHOOK_URL is not None and len(TEAMS_WEBHOOK_URL) > 0


async def send_teams_notification(
    title: str,
    message: str,
    color: str = "0076D7",
    facts: Optional[list] = None
) -> bool:
    """
    Envia notificação para o Microsoft Teams.

    Args:
        title: Título da mensagem
        message: Texto da mensagem
        color: Cor da borda (hex sem #). Padrões:
               - Verde: "2DC72D"
               - Amarelo: "FFC107"
               - Vermelho: "DC3545"
               - Azul: "0076D7"
        facts: Lista de {"name": "Label", "value": "Valor"} para mostrar como tabela

    Returns:
        True se enviou com sucesso, False caso contrário
    """
    if not is_teams_enabled():
        log_info("Teams webhook não configurado, notificação ignorada")
        return False

    # Formato Adaptive Card para Teams
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "sections": [{
            "activityTitle": title,
            "activitySubtitle": message,
            "facts": facts or [],
            "markdown": True
        }]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TEAMS_WEBHOOK_URL,
                json=payload,
                timeout=10.0
            )

            if response.status_code == 200:
                log_info(f"Notificação Teams enviada: {title}")
                return True
            else:
                log_error(f"Erro Teams HTTP {response.status_code}: {response.text}")
                return False

    except Exception as e:
        log_error(f"Erro ao enviar notificação Teams: {e}")
        return False


async def notify_demand_started(name: str, card: str, category: str) -> bool:
    """Notifica que uma demanda foi iniciada."""
    return await send_teams_notification(
        title="▶️ Demanda Iniciada",
        message=f"O cronômetro foi iniciado para uma demanda.",
        color="0076D7",
        facts=[
            {"name": "Demanda", "value": name},
            {"name": "Card", "value": card},
            {"name": "Categoria", "value": category}
        ]
    )


async def notify_demand_paused(name: str, card: str, elapsed_time: str) -> bool:
    """Notifica que uma demanda foi pausada."""
    return await send_teams_notification(
        title="⏸️ Demanda Pausada",
        message=f"O cronômetro foi pausado.",
        color="FFC107",
        facts=[
            {"name": "Demanda", "value": name},
            {"name": "Card", "value": card},
            {"name": "Tempo Acumulado", "value": elapsed_time}
        ]
    )


async def notify_demand_finished(
    name: str,
    card: str,
    category: str,
    elapsed_time: str,
    description: str
) -> bool:
    """Notifica que uma demanda foi finalizada."""
    return await send_teams_notification(
        title="✅ Demanda Finalizada",
        message=f"Uma demanda foi concluída!",
        color="2DC72D",
        facts=[
            {"name": "Demanda", "value": name},
            {"name": "Card", "value": card},
            {"name": "Categoria", "value": category},
            {"name": "Tempo Total", "value": elapsed_time},
            {"name": "Descrição", "value": description or "-"}
        ]
    )


async def notify_demand_deleted(name: str, card: str) -> bool:
    """Notifica que uma demanda foi excluída."""
    return await send_teams_notification(
        title="🗑️ Demanda Excluída",
        message=f"Uma demanda foi removida do sistema.",
        color="DC3545",
        facts=[
            {"name": "Demanda", "value": name},
            {"name": "Card", "value": card}
        ]
    )
