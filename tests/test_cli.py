from langchain_core.messages import HumanMessage

from assistente.cli import main
from assistente.grafo import costruisci_grafo
from tests.conftest import ModelloFinto

ENV = {"LMSTUDIO_BASE_URL": "http://x/v1", "LMSTUDIO_MODEL": "m1"}


def esegui(env, domande, modello=None, elenco=("m1",)):
    righe = iter(domande)
    uscite = []

    def input_fn(_prompt=""):
        try:
            return next(righe)
        except StopIteration:
            raise EOFError

    codice = main(
        env=env,
        input_fn=input_fn,
        stampa=uscite.append,
        elenca=lambda _url: list(elenco),
        crea=lambda cfg, id_modello, strumenti=(): modello,
    )
    return codice, uscite


def test_cronologia_tra_due_domande():
    modello = ModelloFinto(["r1", "r2"])
    codice, _ = esegui(ENV, ["d1", "d2"], modello)
    assert codice == 0
    seconda = [m.content for m in modello.ricevuti[1] if m.type != "system"]
    assert seconda == ["d1", "r1", "d2"]


def test_exit_termina():
    modello = ModelloFinto(["r1"])
    codice, _ = esegui(ENV, ["d1", "exit", "d2"], modello)
    assert codice == 0
    assert len(modello.ricevuti) == 1


def test_errore_connessione_sessione_continua():
    modello = ModelloFinto([ConnectionError("giu"), "ok"])
    codice, uscite = esegui(ENV, ["d1", "d2"], modello)
    assert codice == 0
    assert any("giu" in str(u) for u in uscite)
    secondo = [m.content for m in modello.ricevuti[1] if m.type != "system"]
    assert secondo == ["d2"]


def test_modello_assente_elenca_ids():
    codice, uscite = esegui({"LMSTUDIO_BASE_URL": "http://x/v1"}, [], elenco=("a/b", "c/d"))
    assert codice != 0
    testo = " ".join(map(str, uscite))
    assert "a/b" in testo and "c/d" in testo


def test_modello_non_in_elenco():
    codice, uscite = esegui(ENV, [], elenco=("altro",))
    assert codice != 0
    assert "m1" in " ".join(map(str, uscite))


def test_base_url_mancante():
    codice, uscite = esegui({}, [])
    assert codice != 0
    assert "LMSTUDIO_BASE_URL" in " ".join(map(str, uscite))


def test_elenco_non_raggiungibile():
    from assistente.modello import ErroreModello

    def elenca(_url):
        raise ErroreModello("LM Studio non raggiungibile")

    codice = main(env=ENV, input_fn=input, stampa=lambda _: None, elenca=elenca, crea=None)
    assert codice != 0


def test_prompt_sistema_inviato_ma_non_salvato():
    modello = ModelloFinto(["r"])
    stato = costruisci_grafo(modello).invoke({"messaggi": [HumanMessage("d")], "passaggi": 0})
    assert modello.ricevuti[0][0].type == "system"
    assert all(m.type != "system" for m in stato["messaggi"])
