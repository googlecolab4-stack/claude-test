import httpx
from langchain_openai import ChatOpenAI

from assistente.config import Configurazione


class ErroreModello(Exception):
    pass


def elenca_modelli(base_url: str) -> list[str]:
    url = base_url.rstrip("/") + "/models"
    try:
        risposta = httpx.get(url, timeout=5)
        risposta.raise_for_status()
        return [m["id"] for m in risposta.json()["data"]]
    except (httpx.HTTPError, KeyError, ValueError) as errore:
        raise ErroreModello(f"LM Studio non raggiungibile o risposta non valida ({url}): {errore}")


def scegli_modello(cfg: Configurazione, disponibili: list[str]) -> str:
    elenco = ", ".join(disponibili) or "(nessuno)"
    if cfg.modello is None:
        raise ErroreModello(f"Imposta LMSTUDIO_MODEL con uno di questi id: {elenco}")
    if cfg.modello not in disponibili:
        raise ErroreModello(f"Il modello {cfg.modello!r} non è presente sul server. Disponibili: {elenco}")
    return cfg.modello


def crea_modello(cfg: Configurazione, id_modello: str, strumenti=()):
    # LM Studio non richiede una chiave: il client ne pretende comunque una.
    modello = ChatOpenAI(base_url=cfg.base_url, model=id_modello, api_key="lm-studio")
    return modello.bind_tools(list(strumenti)) if strumenti else modello
