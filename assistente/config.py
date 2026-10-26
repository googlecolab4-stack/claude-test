import os
from collections.abc import Mapping
from dataclasses import dataclass


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
    return Configurazione(
        base_url=base_url,
        modello=env.get("LMSTUDIO_MODEL", "").strip() or None,
        max_passaggi=max_passaggi,
        log_level=env.get("LOG_LEVEL", "INFO").upper(),
    )
