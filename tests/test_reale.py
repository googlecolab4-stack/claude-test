"""Prove reali: richiedono LM Studio attivo. Si lanciano con `pytest -m reale`."""
import os

import pytest

from assistente.config import leggi_configurazione
from assistente.grafo import costruisci_grafo
from assistente.modello import crea_modello, elenca_modelli, scegli_modello
from langchain_core.messages import HumanMessage

pytestmark = pytest.mark.reale

if not (os.environ.get("LMSTUDIO_BASE_URL") and os.environ.get("LMSTUDIO_MODEL")):
    pytest.skip("servono LMSTUDIO_BASE_URL e LMSTUDIO_MODEL", allow_module_level=True)


def test_risposta_non_vuota():
    cfg = leggi_configurazione(os.environ)
    id_modello = scegli_modello(cfg, elenca_modelli(cfg.base_url))
    grafo = costruisci_grafo(crea_modello(cfg, id_modello))
    stato = grafo.invoke({"messaggi": [HumanMessage("Rispondi solo: ok")], "passaggi": 0})
    assert stato["messaggi"][-1].content.strip()


def test_modello_richiede_strumento():
    from langchain_core.messages import ToolMessage

    from assistente.strumenti import STRUMENTI

    cfg = leggi_configurazione(os.environ)
    id_modello = scegli_modello(cfg, elenca_modelli(cfg.base_url))
    grafo = costruisci_grafo(crea_modello(cfg, id_modello, STRUMENTI), cfg.max_passaggi)
    stato = grafo.invoke({"messaggi": [HumanMessage("Che ore sono a Roma adesso?")], "passaggi": 0})
    risultati = [m for m in stato["messaggi"] if isinstance(m, ToolMessage)]
    assert risultati, "il modello non ha richiesto lo strumento orologio"
    assert risultati[0].name == "ora_corrente"
