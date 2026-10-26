import pytest

from assistente.config import ErroreConfigurazione, leggi_configurazione
from assistente.modello import ErroreModello, scegli_modello

BASE = {"LMSTUDIO_BASE_URL": "http://localhost:1234/v1"}


def test_base_url_mancante():
    with pytest.raises(ErroreConfigurazione, match="LMSTUDIO_BASE_URL"):
        leggi_configurazione({})


def test_valori_predefiniti():
    cfg = leggi_configurazione(BASE)
    assert cfg.base_url == "http://localhost:1234/v1"
    assert cfg.modello is None
    assert cfg.max_passaggi == 5
    assert cfg.log_level == "INFO"


@pytest.mark.parametrize("valore", ["0", "abc", "-1"])
def test_max_passaggi_non_valido(valore):
    with pytest.raises(ErroreConfigurazione, match="MAX_PASSAGGI"):
        leggi_configurazione({**BASE, "MAX_PASSAGGI": valore})


def test_modello_assente_elenca_gli_id():
    cfg = leggi_configurazione(BASE)
    with pytest.raises(ErroreModello, match="a/b.*c/d"):
        scegli_modello(cfg, ["a/b", "c/d"])


def test_modello_non_in_elenco():
    cfg = leggi_configurazione({**BASE, "LMSTUDIO_MODEL": "x/y"})
    with pytest.raises(ErroreModello, match="x/y.*a/b"):
        scegli_modello(cfg, ["a/b"])


def test_modello_presente():
    cfg = leggi_configurazione({**BASE, "LMSTUDIO_MODEL": "a/b"})
    assert scegli_modello(cfg, ["a/b", "c/d"]) == "a/b"


def test_log_level_non_valido():
    with pytest.raises(ErroreConfigurazione, match="LOG_LEVEL"):
        leggi_configurazione({**BASE, "LOG_LEVEL": "verbose"})


def test_log_level_minuscolo_accettato():
    assert leggi_configurazione({**BASE, "LOG_LEVEL": "debug"}).log_level == "DEBUG"
