from langchain_core.messages import AIMessage


class ModelloFinto:
    """Modello con risposte scritte a mano; un elemento Exception viene sollevato."""

    def __init__(self, risposte):
        self.risposte = list(risposte)
        self.ricevuti = []

    def invoke(self, messaggi):
        self.ricevuti.append(list(messaggi))
        prossima = self.risposte.pop(0)
        if isinstance(prossima, Exception):
            raise prossima
        return prossima if isinstance(prossima, AIMessage) else AIMessage(prossima)
