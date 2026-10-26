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

## Configurazione
Solo variabili d'ambiente (vedi `.env.example`):

| Variabile | Significato |
|---|---|
| `LMSTUDIO_BASE_URL` | obbligatoria, es. `http://localhost:1234/v1` |
| `LMSTUDIO_MODEL` | id del modello come restituito da `GET /v1/models` |
| `MAX_PASSAGGI` | limite di turni del modello per domanda (default 5) |
| `LOG_LEVEL` | livello dei log su stderr (default `INFO`) |

## Avvio (PowerShell, LM Studio acceso con il server locale attivo)
```powershell
$env:LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
python -m assistente          # senza LMSTUDIO_MODEL elenca gli id disponibili ed esce (codice 2)
$env:LMSTUDIO_MODEL = "google/gemma-4-e2b"
python -m assistente          # 'exit' o Ctrl+D per uscire; la cronologia vale solo per la sessione
```

## Prova reale con LM Studio
```powershell
python -m pytest -m reale -v   # richiede LMSTUDIO_BASE_URL e LMSTUDIO_MODEL
```

## Diagnosi
- `Errore: Variabile LMSTUDIO_BASE_URL mancante`: imposta la variabile.
- `LM Studio non raggiungibile`: avvia il server locale in LM Studio e controlla la porta.
- `Il modello ... non è presente sul server`: usa uno degli id elencati.
