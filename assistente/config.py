import os
from collections.abc import Mapping
from dataclasses import dataclass


LIVELLI_LOG = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ErroreConfigurazione(Exception):
    pass


@dataclass(frozen=True)
class Configurazione:
    base_url: str
    modello: str | None
    max_passaggi: int
    log_level: str


def leggi_configurazione(env: Mapping[str, str] = os.environ) -> Configurazione:
    base_url = env.get("LMSTUDIO_BASE_URL", "").strip()
    if not base_url:
        raise ErroreConfigurazione(
            "Variabile LMSTUDIO_BASE_URL mancante (es. http://localhost:1234/v1)."
        )
    grezzo = env.get("MAX_PASSAGGI", "5")
    try:
        max_passaggi = int(grezzo)
    except ValueError:
        max_passaggi = 0
    if max_passaggi < 1:
        raise ErroreConfigurazione(f"MAX_PASSAGGI deve essere un intero >= 1 (ricevuto {grezzo!r}).")
    log_level = env.get("LOG_LEVEL", "INFO").upper()
    if log_level not in LIVELLI_LOG:
        raise ErroreConfigurazione(f"LOG_LEVEL non valido: {log_level!r} (usa {', '.join(sorted(LIVELLI_LOG))}).")
    return Configurazione(
        base_url=base_url,
        modello=env.get("LMSTUDIO_MODEL", "").strip() or None,
        max_passaggi=max_passaggi,
        log_level=log_level,
    )
