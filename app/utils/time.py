# app/utils/time.py
"""
Utilidad centralizada para manejo de fechas.
Reemplaza datetime.utcnow() (deprecado en Python 3.12+).
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Devuelve la fecha/hora actual en UTC con timezone-aware.
    Reemplazo directo de datetime.utcnow().
    """
    return datetime.now(timezone.utc)