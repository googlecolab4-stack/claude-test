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
