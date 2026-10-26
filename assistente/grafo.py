import logging
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from assistente.strumenti import STRUMENTI

log = logging.getLogger(__name__)

PROMPT_SISTEMA = (
    "Sei un assistente del laboratorio. Rispondi in italiano in modo breve e chiaro. "
    "Per conoscere data e ora usa lo strumento orologio, se disponibile."
)
MESSAGGIO_LIMITE = "Ho raggiunto il limite di passaggi per questa domanda: riprova con una richiesta più semplice."


class Stato(TypedDict):
    messaggi: Annotated[list[BaseMessage], add_messages]
    passaggi: int


class ModelloFisso:
    """Modello che risponde sempre con lo stesso testo, senza rete."""

    def __init__(self, risposta: str = "Risposta fissa"):
        self.risposta = risposta

    def invoke(self, messaggi: list[BaseMessage]) -> AIMessage:
        return AIMessage(self.risposta)


def costruisci_grafo(modello, max_passaggi: int = 5, strumenti=STRUMENTI):
    per_nome = {s.name: s for s in strumenti}

    def nodo_modello(stato: Stato) -> dict:
        risposta = modello.invoke([SystemMessage(PROMPT_SISTEMA), *stato["messaggi"]])
        return {"messaggi": [risposta], "passaggi": stato["passaggi"] + 1}

    def nodo_strumenti(stato: Stato) -> dict:
        risultati = []
        for richiesta in stato["messaggi"][-1].tool_calls:
            nome, argomenti = richiesta["name"], richiesta["args"]
            log.info("Chiamata strumento %s con argomenti %s", nome, argomenti)
            strumento = per_nome.get(nome)
            if strumento is None:
                esito = f"Errore: strumento sconosciuto: {nome}"
            else:
                try:
                    esito = str(strumento.invoke(argomenti))
                except Exception as errore:
                    esito = f"Errore: argomenti non validi per {nome}: {errore}"
            log.info("Risultato strumento %s: %s", nome, esito)
            risultati.append(ToolMessage(esito, tool_call_id=richiesta["id"], name=nome))
        return {"messaggi": risultati}

    def nodo_limite(stato: Stato) -> dict:
        ultimo = stato["messaggi"][-1]
        log.warning("Limite di %d passaggi raggiunto", max_passaggi)
        # Stesso id: add_messages sostituisce il messaggio, togliendo le richieste senza risposta.
        senza_richieste = AIMessage(content=ultimo.content, id=ultimo.id)
        return {"messaggi": [senza_richieste, AIMessage(MESSAGGIO_LIMITE)]}

    def dopo_modello(stato: Stato) -> Literal["strumenti", "limite", "fine"]:
        if not stato["messaggi"][-1].tool_calls:
            return "fine"
        return "strumenti" if stato["passaggi"] < max_passaggi else "limite"

    grafo = StateGraph(Stato)
    grafo.add_node("modello", nodo_modello)
    grafo.add_node("strumenti", nodo_strumenti)
    grafo.add_node("limite", nodo_limite)
    grafo.add_edge(START, "modello")
    grafo.add_conditional_edges("modello", dopo_modello, {"strumenti": "strumenti", "limite": "limite", "fine": END})
    grafo.add_edge("strumenti", "modello")
    grafo.add_edge("limite", END)
    return grafo.compile()
