from datetime import datetime, timezone

from assistente.strumenti import STRUMENTI, ora_corrente, ora_corrente_a


def test_inverno_a_roma():
    adesso = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    assert "2026-01-15T13:00:00+01:00" in ora_corrente_a("Europe/Rome", adesso)


def test_estate_a_roma():
    adesso = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
    assert "2026-07-15T14:00:00+02:00" in ora_corrente_a("Europe/Rome", adesso)


def test_fuso_non_valido():
    adesso = datetime(2026, 1, 15, tzinfo=timezone.utc)
    assert ora_corrente_a("Mars/Olympus", adesso).startswith("Errore: fuso orario non valido")


def test_fuso_vuoto():
    adesso = datetime(2026, 1, 15, tzinfo=timezone.utc)
    assert ora_corrente_a("", adesso).startswith("Errore: fuso orario non valido")


def test_strumento_langchain_esposto():
    assert [t.name for t in STRUMENTI] == ["ora_corrente"]
    assert "Europe/Rome" in ora_corrente.invoke({"fuso_orario": "Europe/Rome"})
