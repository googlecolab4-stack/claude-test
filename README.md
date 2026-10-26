# Assistente del laboratorio

Applicazione da terminale con un grafo LangGraph esplicito che conversa con un modello
servito da LM Studio. Lavori in corso: vedere `docs/superpowers/` per specifica e piano.

## Ambiente (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Test automatici (senza modello)
```powershell
python -m pytest
```
Le prove che richiedono LM Studio hanno il marcatore `reale` e sono escluse di default.
