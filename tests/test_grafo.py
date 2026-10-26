from langchain_core.messages import AIMessage, HumanMessage

from assistente.grafo import ModelloFisso, costruisci_grafo


def test_risposta_fissa():
    grafo = costruisci_grafo(ModelloFisso("ciao"))
    stato = grafo.invoke({"messaggi": [HumanMessage("hey")], "passaggi": 0})
    assert stato["messaggi"][-1].content == "ciao"


def test_messaggi_accumulati():
    grafo = costruisci_grafo(ModelloFisso("ciao"))
    stato = grafo.invoke({"messaggi": [HumanMessage("hey")], "passaggi": 0})
    assert [type(m) for m in stato["messaggi"]] == [HumanMessage, AIMessage]


# --- strumenti e instradamento -------------------------------------------------
import logging

from langchain_core.messages import ToolMessage

from assistente.cli import esegui_domanda
from assistente.grafo import MESSAGGIO_LIMITE
from tests.conftest import ModelloFinto


def richiesta(*fusi, prefisso="c"):
    return AIMessage(
        "",
        tool_calls=[
            {"name": "ora_corrente", "args": {"fuso_orario": f}, "id": f"{prefisso}{i}"}
            for i, f in enumerate(fusi)
        ],
    )


def parte(modello, **kw):
    return costruisci_grafo(modello, **kw).invoke({"messaggi": [HumanMessage("ora?")], "passaggi": 0})


def senza_risposta(messaggi):
    risposti = {m.tool_call_id for m in messaggi if isinstance(m, ToolMessage)}
    return [c["id"] for m in messaggi if isinstance(m, AIMessage) for c in m.tool_calls if c["id"] not in risposti]


def test_senza_strumento_termina():
    modello = ModelloFinto(["ciao"])
    stato = parte(modello)
    assert len(modello.ricevuti) == 1
    assert not any(isinstance(m, ToolMessage) for m in stato["messaggi"])


def test_ciclo_strumento_modello_risposta():
    modello = ModelloFinto([richiesta("Europe/Rome"), "Sono le 13"])
    stato = parte(modello)
    tipi = [type(m) for m in stato["messaggi"]]
    assert tipi == [HumanMessage, AIMessage, ToolMessage, AIMessage]
    assert "Europe/Rome" in stato["messaggi"][2].content
    assert stato["messaggi"][-1].content == "Sono le 13"


def test_due_richieste_in_una_risposta():
    stato = parte(ModelloFinto([richiesta("Europe/Rome", "Asia/Tokyo"), "fatto"]))
    risultati = [m for m in stato["messaggi"] if isinstance(m, ToolMessage)]
    assert [m.tool_call_id for m in risultati] == ["c0", "c1"]


def test_strumento_sconosciuto_e_argomenti_errati():
    sbagliata = AIMessage(
        "",
        tool_calls=[
            {"name": "inesistente", "args": {}, "id": "a"},
            {"name": "ora_corrente", "args": {}, "id": "b"},
            {"name": "ora_corrente", "args": {"fuso_orario": "Mars/Olympus"}, "id": "c"},
        ],
    )
    stato = parte(ModelloFinto([sbagliata, "ok"]))
    risultati = [m.content for m in stato["messaggi"] if isinstance(m, ToolMessage)]
    assert len(risultati) == 3 and all(r.startswith("Errore") for r in risultati)
    assert stato["messaggi"][-1].content == "ok"


def test_limite_passaggi():
    modello = ModelloFinto([richiesta("Europe/Rome", prefisso=f"p{i}") for i in range(3)])
    stato = parte(modello, max_passaggi=3)
    assert len(modello.ricevuti) == 3
    assert stato["messaggi"][-1].content == MESSAGGIO_LIMITE
    assert senza_risposta(stato["messaggi"]) == []


def test_cronologia_valida_dopo_limite():
    modello = ModelloFinto([richiesta("Europe/Rome", prefisso=f"p{i}") for i in range(2)] + ["dopo"])
    grafo = costruisci_grafo(modello, max_passaggi=2)
    cronologia, _ = esegui_domanda(grafo, [], "prima")
    assert senza_risposta(cronologia) == []
    cronologia, risposta = esegui_domanda(grafo, cronologia, "seconda")
    assert risposta == "dopo"
    assert senza_risposta(modello.ricevuti[2]) == []


def test_passaggi_riparte_per_domanda():
    modello = ModelloFinto([richiesta("Europe/Rome"), "uno", richiesta("Europe/Rome", prefisso="q"), "due"])
    grafo = costruisci_grafo(modello, max_passaggi=2)
    cronologia, r1 = esegui_domanda(grafo, [], "a")
    _, r2 = esegui_domanda(grafo, cronologia, "b")
    assert (r1, r2) == ("uno", "due")


def test_log_chiamata_strumento(caplog):
    with caplog.at_level(logging.INFO):
        parte(ModelloFinto([richiesta("Europe/Rome"), "ok"]))
    testo = caplog.text
    assert "ora_corrente" in testo and "Europe/Rome" in testo
