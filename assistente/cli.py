import logging
import os
import sys

import openai
from langchain_core.messages import BaseMessage, HumanMessage

from assistente.config import ErroreConfigurazione, leggi_configurazione
from assistente.grafo import costruisci_grafo
from assistente.modello import ErroreModello, crea_modello, elenca_modelli, scegli_modello

USCITA = {"exit", "esci"}


def esegui_domanda(grafo, cronologia: list[BaseMessage], testo: str) -> tuple[list[BaseMessage], str]:
    stato = grafo.invoke({"messaggi": [*cronologia, HumanMessage(testo)], "passaggi": 0})
    messaggi = stato["messaggi"]
    return messaggi, str(messaggi[-1].content)


def main(env=os.environ, input_fn=input, stampa=print, elenca=elenca_modelli, crea=crea_modello) -> int:
    try:
        cfg = leggi_configurazione(env)
        logging.basicConfig(level=cfg.log_level, stream=sys.stderr, format="%(levelname)s %(name)s: %(message)s")
        id_modello = scegli_modello(cfg, elenca(cfg.base_url))
    except (ErroreConfigurazione, ErroreModello) as errore:
        stampa(f"Errore: {errore}")
        return 2

    grafo = costruisci_grafo(crea(cfg, id_modello))
    cronologia: list[BaseMessage] = []
    stampa(f"Modello: {id_modello}. Scrivi 'exit' o premi Ctrl+D per uscire.")
    while True:
        try:
            testo = input_fn("> ").strip()
        except EOFError:
            return 0
        if testo.lower() in USCITA:
            return 0
        if not testo:
            continue
        try:
            cronologia, risposta = esegui_domanda(grafo, cronologia, testo)
        except (ConnectionError, openai.OpenAIError) as errore:
            stampa(f"Errore di comunicazione con LM Studio: {errore}")
            continue
        stampa(risposta)
