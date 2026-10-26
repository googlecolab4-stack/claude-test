from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


PROMPT_SISTEMA = (
    "Sei un assistente del laboratorio. Rispondi in italiano in modo breve e chiaro. "
    "Per conoscere data e ora usa lo strumento orologio, se disponibile."
)


class Stato(TypedDict):
    messaggi: Annotated[list[BaseMessage], add_messages]
    passaggi: int


class ModelloFisso:
    """Modello che risponde sempre con lo stesso testo, senza rete."""

    def __init__(self, risposta: str = "Risposta fissa"):
        self.risposta = risposta

    def invoke(self, messaggi: list[BaseMessage]) -> AIMessage:
        return AIMessage(self.risposta)


def costruisci_grafo(modello):
    def nodo_modello(stato: Stato) -> dict:
        risposta = modello.invoke([SystemMessage(PROMPT_SISTEMA), *stato["messaggi"]])
        return {"messaggi": [risposta], "passaggi": stato["passaggi"] + 1}

    grafo = StateGraph(Stato)
    grafo.add_node("modello", nodo_modello)
    grafo.add_edge(START, "modello")
    grafo.add_edge("modello", END)
    return grafo.compile()
