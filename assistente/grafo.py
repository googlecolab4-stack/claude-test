from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


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
        risposta = modello.invoke(stato["messaggi"])
        return {"messaggi": [risposta], "passaggi": stato["passaggi"] + 1}

    grafo = StateGraph(Stato)
    grafo.add_node("modello", nodo_modello)
    grafo.add_edge(START, "modello")
    grafo.add_edge("modello", END)
    return grafo.compile()
