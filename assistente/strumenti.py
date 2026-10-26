from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.tools import tool


def ora_corrente_a(fuso_orario: str, adesso: datetime) -> str:
    """Formatta l'istante `adesso` nel fuso indicato; errore leggibile se il fuso non esiste."""
    try:
        fuso = ZoneInfo(fuso_orario)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return f"Errore: fuso orario non valido: {fuso_orario!r}"
    return f"{adesso.astimezone(fuso).isoformat(timespec='seconds')} ({fuso_orario})"


@tool
def ora_corrente(fuso_orario: str) -> str:
    """Restituisce data e ora attuali nel fuso orario richiesto.
    `fuso_orario` è obbligatorio ed è un nome IANA, per esempio 'Europe/Rome' o 'Asia/Tokyo'."""
    return ora_corrente_a(fuso_orario, datetime.now(timezone.utc))


STRUMENTI = [ora_corrente]
