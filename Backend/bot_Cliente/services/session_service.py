"""
Session Service
Gestión del estado de sesión de usuarios del bot.
"""
import requests
import logging
from ..config import (
    SESSION_URL,
    SESSION_UPDATE_URL,
    SESSION_RESET_URL,
    CURRENCY_RATES_URL,
    DEFAULT_EXCHANGE_RATE
)


def get_session(telegram_id: int) -> dict:
    """
    Obtiene la sesión actual del usuario.
    
    Args:
        telegram_id: ID de Telegram del usuario
    
    Returns:
        Dict con state y temp_data
    """
    try:
        r = requests.get(f"{SESSION_URL}{telegram_id}/", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"DEBUG [get_session] Error: {e}")
    return {"state": "IDLE", "temp_data": {}}


def update_session(telegram_id: int, state: str = None, current_product_id: int = None, temp_data: dict = None):
    """
    Actualiza la sesión del usuario.
    
    Args:
        telegram_id: ID de Telegram
        state: Nuevo estado (opcional)
        current_product_id: ID del producto actual (opcional)
        temp_data: Datos temporales (opcional)
    """
    payload = {}
    if state: 
        payload["state"] = state
    if current_product_id: 
        payload["current_product_id"] = current_product_id
    if temp_data: 
        payload["temp_data"] = temp_data
    
    try:
        print(f"DEBUG [update_session] Updating {telegram_id} -> {payload}")
        requests.post(f"{SESSION_UPDATE_URL}{telegram_id}/", json=payload, timeout=2)
    except Exception as e:
        print(f"DEBUG [update_session] Error: {e}")


def reset_session(telegram_id: int):
    """
    Resetea la sesión del usuario a IDLE.
    
    Args:
        telegram_id: ID de Telegram
    """
    try:
        requests.post(f"{SESSION_RESET_URL}{telegram_id}/", timeout=2)
    except: 
        pass


def get_exchange_rate() -> float:
    """
    Obtiene la tasa de cambio VES del backend.
    
    Returns:
        Tasa de cambio o fallback de 35.0
    """
    try:
        r = requests.get(CURRENCY_RATES_URL, timeout=3)
        if r.status_code == 200:
            return float(r.json().get("VES", DEFAULT_EXCHANGE_RATE))
    except Exception as e:
        logging.error(f"Error obteniendo tasa: {e}")
    return DEFAULT_EXCHANGE_RATE
