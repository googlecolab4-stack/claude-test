# Assistente del laboratorio — piano di implementazione

> **Per gli esecutori:** usare superpowers:subagent-driven-development (consigliato) o superpowers:executing-plans, task per task. I passi usano caselle `- [ ]`.

**Obiettivo:** applicazione da terminale con grafo LangGraph esplicito che conversa con LM Studio, conserva la cronologia di sessione e usa lo strumento orologio via tool calling, avviabile anche con Docker Compose.

**Architettura:** pacchetto `assistente/` con moduli piccoli e sincroni (`config`, `modello`, `strumenti`, `grafo`, `cli`). Il grafo ha due nodi (`modello`, `strumenti`) e un instradamento condizionale; la CLI tiene la lista dei messaggi e la passa al grafo a ogni domanda.

**Stack:** Python 3.11, `langgraph`, `langchain-openai`, `tzdata`, `pytest`.

**Specifica:** `docs/superpowers/specs/2026-10-26-assistente-laboratorio-design.md`

## Vincoli globali
- Progetto nella radice di `repo-lab-llm/`; `lezione tre/` non si legge né si modifica.
- Solo variabili d'ambiente: `LMSTUDIO_BASE_URL` (obbligatoria, nessun default nel codice), `LMSTUDIO_MODEL` (opzionale, mai inventata), `MAX_PASSAGGI` (default 5), `LOG_LEVEL` (default INFO).
- Se `LMSTUDIO_MODEL` manca, si elencano gli id di `GET /v1/models` e si esce; non se ne sceglie uno.
- Niente persistenza, checkpointer, streaming, MCP, RAG, altri strumenti, interfacce grafiche.
- Dipendenze con versione fissata (`==`); le versioni si verificano con `pip install` nel Task 1 e si scrivono in `requirements.txt` / `requirements-dev.txt`.
- Commit Conventional in italiano, un commit per task, dopo `git status` + controllo del diff + staging dei soli file pertinenti; nessun push; mai `.env`, venv, cache.
- Test automatici senza modello; prove reali separate (marcatore `reale`, escluso di default).
- Comandi del README anche per PowerShell, solo se verificati; il resoconto di ogni task dice cosa è stato eseguito, con quale esito e cosa resta da provare.

## Punti da non trascurare (Review Focus)
1. Limite raggiunto con richieste di strumento pendenti: la cronologia deve restare valida alla domanda successiva (Task 2/3).
2. Più richieste di strumento in una sola risposta: un `ToolMessage` ciascuna (Task 3).
3. Strumento sconosciuto o argomenti errati / fuso non valido: errore leggibile, nessuna eccezione (Task 3).
4. LM Studio non raggiungibile durante la sessione: messaggio, domanda scartata, sessione viva (Task 2).
5. `LMSTUDIO_MODEL` impostata ma assente dall'elenco, o `LMSTUDIO_BASE_URL` mancante: errore chiaro (Task 2).

## Struttura dei file
```
assistente/__init__.py   assistente/config.py   assistente/modello.py
assistente/strumenti.py  assistente/grafo.py    assistente/cli.py   assistente/__main__.py
tests/conftest.py  tests/test_grafo.py  tests/test_config.py  tests/test_cli.py
tests/test_strumenti.py  tests/test_reale.py
requirements.txt  requirements-dev.txt  pytest.ini  .gitignore  .env.example
Dockerfile  .dockerignore  compose.yaml  README.md
```

---

## Task 1: Grafo con risposta fissa

**Comportamento:** un grafo con stato e nodo `modello` che risponde con testo fisso, senza rete.

**File:**
- Create: `assistente/__init__.py`, `assistente/grafo.py`, `tests/test_grafo.py`, `requirements.txt`, `requirements-dev.txt`, `pytest.ini` (`testpaths = tests`, `addopts = -m "not reale"`, marcatore `reale` registrato), `.gitignore` (`.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`), `README.md` (bozza: scopo, ambiente PowerShell, `pytest`).

**Interfaces — Produces:**
- `class Stato(TypedDict): messaggi: Annotated[list[BaseMessage], add_messages]; passaggi: int`
- `costruisci_grafo(modello) -> CompiledStateGraph`, dove `modello` è un oggetto con `.invoke(list[BaseMessage]) -> AIMessage`.
- `class ModelloFisso: def __init__(self, risposta: str = "Risposta fissa")` con `.invoke(...)` che restituisce `AIMessage(risposta)`.

- [ ] **Passo 1: creare venv, installare `langgraph`, `langchain-openai`, `tzdata`, `pytest`; fissare le versioni installate** in `requirements.txt` (runtime) e `requirements-dev.txt` (`-r requirements.txt` + pytest). Comando: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install ...; pip freeze` (copiare solo i pacchetti diretti).
- [ ] **Passo 2: test che fallisce** in `tests/test_grafo.py`: `test_risposta_fissa` — `costruisci_grafo(ModelloFisso("ciao")).invoke({"messaggi":[HumanMessage("hey")], "passaggi":0})["messaggi"][-1].content == "ciao"`; `test_messaggi_accumulati` — la lista finale è `[Human, AI]`.
- [ ] **Passo 3: eseguire** `pytest tests/test_grafo.py -v` → FAIL (import).
- [ ] **Passo 4: implementare** `Stato`, `ModelloFisso`, nodo `modello` (invoca il modello, restituisce `{"messaggi":[risposta], "passaggi": passaggi+1}`) e `costruisci_grafo` con `START → modello → END`.
- [ ] **Passo 5: eseguire** `pytest -v` → PASS.
- [ ] **Passo 6: README** con struttura iniziale e comando di test verificato; **commit** `feat(grafo): aggiunge il grafo con risposta fissa` (aggiungere solo i file elencati).

**Test senza modello:** tutti. **Prove reali:** nessuna.

---

## Task 2: Collegamento a LM Studio, configurazione, cronologia e CLI

**Comportamento:** la CLI chiede una domanda, il grafo interroga LM Studio, la cronologia si accumula in memoria; configurazione ed errori chiari.

**File:**
- Create: `assistente/config.py`, `assistente/modello.py`, `assistente/cli.py`, `assistente/__main__.py`, `.env.example`, `tests/conftest.py`, `tests/test_config.py`, `tests/test_cli.py`, `tests/test_reale.py`
- Modify: `assistente/grafo.py` (limite, prompt di sistema), `tests/test_grafo.py`, `README.md`

**Interfaces — Produces:**
- `config.py`: `@dataclass Configurazione(base_url: str, modello: str | None, max_passaggi: int, log_level: str)`; `leggi_configurazione(env: Mapping[str,str] = os.environ) -> Configurazione` (solleva `ErroreConfigurazione` se manca `LMSTUDIO_BASE_URL` o `MAX_PASSAGGI` non è un intero ≥ 1).
- `modello.py`: `elenca_modelli(base_url: str) -> list[str]` (GET `/models`, errori di rete → `ErroreModello`); `scegli_modello(cfg) -> str` (assente → `ErroreModello` con l'elenco; non presente nell'elenco → errore con l'elenco); `crea_modello(cfg, id_modello, strumenti=()) -> Runnable` (`ChatOpenAI(base_url=..., model=..., api_key="lm-studio")`, `bind_tools` solo se `strumenti`).
- `grafo.py`: `PROMPT_SISTEMA` (italiano, breve) anteposto a ogni invocazione senza salvarlo nello stato; `costruisci_grafo(modello, max_passaggi: int = 5)`; `MESSAGGIO_LIMITE` costante.
- `cli.py`: `esegui_domanda(grafo, cronologia: list[BaseMessage], testo: str) -> tuple[list[BaseMessage], str]`; `main(env=os.environ, input_fn=input, stampa=print) -> int`.
- `conftest.py`: `ModelloFinto(risposte: list[AIMessage])` che registra i messaggi ricevuti e restituisce le risposte in ordine.

- [ ] **Passo 1: test che falliscono**
  - `test_config.py`: base_url mancante → `ErroreConfigurazione`; default `max_passaggi == 5`; `MAX_PASSAGGI=0` e `abc` → errore.
  - `tests/test_grafo.py` (nuovi): `test_prompt_sistema_inviato_ma_non_salvato` (il primo messaggio visto da `ModelloFinto` è `SystemMessage`; lo stato finale non lo contiene).
  - `test_cli.py` con `ModelloFinto` e `input_fn` simulato: `test_cronologia_tra_due_domande` (alla seconda domanda il modello riceve Human1, AI1, Human2); `test_exit_termina`; `test_errore_connessione_sessione_continua` (modello che solleva `ConnectionError` alla prima domanda: viene stampato un messaggio, la cronologia non contiene la domanda fallita, la seconda domanda funziona); `test_modello_assente_elenca_ids` (`main` esce con codice ≠ 0 e stampa gli id con `elenca_modelli` simulato); `test_modello_non_in_elenco`.
  - `test_reale.py` (`@pytest.mark.reale`, saltato se mancano `LMSTUDIO_BASE_URL`/`LMSTUDIO_MODEL`): una domanda semplice ottiene una risposta non vuota.
- [ ] **Passo 2:** `pytest -v` → FAIL.
- [ ] **Passo 3: implementare** `config.py`, `modello.py`, estensioni di `grafo.py` e `cli.py` (log su stderr con `LOG_LEVEL`; `ConnectionError`/`openai.APIConnectionError` catturati nel ciclo; `Ctrl+D`/`exit` terminano).
- [ ] **Passo 4:** `pytest -v` → PASS (il test `reale` risulta deselezionato).
- [ ] **Passo 5: prova reale (esplicita, non automatica):** con LM Studio acceso, `$env:LMSTUDIO_BASE_URL="http://localhost:1234/v1"; python -m assistente` (senza `LMSTUDIO_MODEL` → elenco id; poi con `google/gemma-4-e2b`), due domande dove la seconda dipende dalla prima; poi `pytest -m reale -v`. Riportare l'esito reale.
- [ ] **Passo 6: README** (configurazione, avvio, diagnosi connessione/modello, comandi PowerShell verificati) e `.env.example` (nomi delle variabili, nessuna credenziale); **commit** `feat(modello): collega LM Studio e conserva la cronologia` (eventualmente separare `test(...)`/`docs:`).

**Test senza modello:** config, grafo, CLI, errori. **Richiede LM Studio:** `test_reale.py` e prova manuale.

---

## Task 3: Strumento orologio e instradamento

**Comportamento:** il modello può chiedere `ora_corrente(fuso_orario)`; il grafo lo esegue, rimanda il risultato al modello, ottiene la risposta finale; chiamate nei log; limite di passaggi.

**File:**
- Create: `assistente/strumenti.py`, `tests/test_strumenti.py`
- Modify: `assistente/grafo.py`, `assistente/cli.py` (collega lo strumento), `tests/test_grafo.py`, `tests/test_reale.py`, `README.md`

**Interfaces:**
- Consumes: `costruisci_grafo(modello, max_passaggi)`, `ModelloFinto`, `crea_modello(cfg, id, strumenti)`.
- Produces: `ora_corrente(fuso_orario: str) -> str` (`@tool` LangChain, descrizione italiana che richiede il nome IANA); `ora_corrente_a(fuso_orario: str, adesso: datetime) -> str` funzione pura usata dallo strumento (istante iniettabile, formato `"<ISO 8601 con offset> (<fuso>)"`; fuso non valido → `"Errore: fuso orario non valido: <valore>"`); `STRUMENTI = [ora_corrente]`; nodo `strumenti` (esegue ogni richiesta, un `ToolMessage` per `tool_call_id`, errore leggibile per strumento sconosciuto o argomenti errati); funzione di instradamento `dopo_modello(stato) -> Literal["strumenti", "fine"]`; nodo `limite` che sostituisce l'ultimo `AIMessage` con una copia senza `tool_calls` e aggiunge `MESSAGGIO_LIMITE`.

- [ ] **Passo 1: test che falliscono**
  - `test_strumenti.py`: `ora_corrente_a("Europe/Rome", datetime(2026,1,15,12,0,tzinfo=UTC))` contiene `13:00:00+01:00`; estate → `+02:00`; `"Mars/Olympus"` → inizia con `"Errore: fuso orario non valido"`; stringa vuota → errore, nessuna eccezione.
  - `test_grafo.py`: `test_senza_strumento_termina` (nessun nodo `strumenti`); `test_ciclo_strumento_modello_risposta` (finto: prima `AIMessage` con `tool_calls=[{"name":"ora_corrente","args":{"fuso_orario":"Europe/Rome"},"id":"1"}]`, poi testo; lo stato contiene Human, AI(tool_calls), ToolMessage, AI); `test_due_richieste_in_una_risposta` (due `ToolMessage` con id corretti); `test_strumento_sconosciuto_e_argomenti_errati` (ToolMessage di errore, nessuna eccezione, il modello poi risponde); `test_limite_passaggi` (finto che chiede sempre lo strumento, `max_passaggi=3`: il modello è invocato 3 volte, l'ultimo messaggio è `MESSAGGIO_LIMITE`, nessun `tool_calls` pendente nei messaggi); `test_cronologia_valida_dopo_limite` (seconda domanda sulla stessa cronologia non lascia `tool_calls` senza `ToolMessage`); `test_passaggi_riparte_per_domanda`; `test_log_chiamata_strumento` (`caplog`: nome e argomenti a INFO).
  - `test_reale.py`: `test_modello_richiede_strumento` (chiede l'ora a Roma; verifica che nello stato finale esista un `ToolMessage` da `ora_corrente`; l'esito negativo va riportato, non mascherato).
- [ ] **Passo 2:** `pytest -v` → FAIL.
- [ ] **Passo 3: implementare** strumenti, nodo `strumenti`, instradamento condizionale (`modello` → `strumenti` se ci sono `tool_calls` e `passaggi < max_passaggi`; → `limite` se ci sono ma il limite è raggiunto; altrimenti → fine; `strumenti` → `modello`), collegare `STRUMENTI` nella CLI.
- [ ] **Passo 4:** `pytest -v` → PASS.
- [ ] **Passo 5: prova reale:** `pytest -m reale -v` e sessione manuale ("Che ore sono a Tokyo?"), controllando nei log la riga della chiamata. Riportare cosa fa davvero `gemma-4-e2b`.
- [ ] **Passo 6: README** (strumento, log, limite, diagnosi del tool calling) e **commit** `feat(strumenti): aggiunge lo strumento orologio e l'instradamento` (con commit `test(strumenti)` separato se comodo).

**Test senza modello:** strumento (istante fisso), instradamento, limite, errori, log. **Richiede LM Studio:** `test_modello_richiede_strumento`, sessione manuale.

---

## Task 4: Docker Compose e verifica completa

**Comportamento:** l'app gira in un container interattivo e raggiunge LM Studio sull'host.

**File:**
- Create: `Dockerfile` (`python:3.11-slim`, installa `requirements.txt`, utente non root, `CMD ["python","-m","assistente"]`), `.dockerignore` (`.venv`, `.git`, `.env`, `docs`, `lezione tre`, cache), `compose.yaml` (servizio `assistente`, `build: .`, `stdin_open: true`, `tty: true`, `env_file: .env`, `LMSTUDIO_BASE_URL` predefinito `http://host.docker.internal:1234/v1`, `extra_hosts: ["host.docker.internal:host-gateway"]`)
- Modify: `.env.example` (valori Docker commentati), `README.md`, `CLAUDE.md` (struttura e comandi di test ora stabili)

- [ ] **Passo 1: verifica statica (senza LM Studio):** `docker compose config` valida; `docker build -t assistente .` riesce; `docker run --rm assistente python -m pytest` non è previsto (le dipendenze di sviluppo non sono nell'immagine) — i test restano locali.
- [ ] **Passo 2: prova reale con Docker (esplicita):** LM Studio acceso, copiare `.env.example` in `.env` e impostare `LMSTUDIO_MODEL`; `docker compose run --rm assistente` → conversazione con cronologia e domanda sull'ora; verificare nei log del container la chiamata allo strumento. Provare anche con `LMSTUDIO_MODEL` assente (elenco id) e con LM Studio spento (messaggio chiaro).
- [ ] **Passo 3: verifica completa finale:** `pytest -v` (automatici), `pytest -m reale -v` (reali locali), prova Docker; `git status` pulito.
- [ ] **Passo 4: README completo** (configurazione, avvio locale e Docker, test automatici e reali, diagnosi, PowerShell, solo comandi eseguiti); aggiornare `CLAUDE.md` solo per convenzioni stabili. **Commit** `feat(docker): aggiunge Docker Compose per l'applicazione` e `docs: completa il README e aggiorna CLAUDE.md`.
- [ ] **Passo 5: resoconto finale** con elenco di cosa è stato eseguito e con quale esito, e cosa resta da provare (es. altri modelli, Docker su Linux).

**Senza modello:** `docker compose config`, build. **Richiede LM Studio e Docker:** prova interattiva nel container.

---

## Auto-revisione
- Copertura della specifica: grafo/stato/instradamento (T1–T3), cronologia (T2), configurazione e errori (T2), strumento, log, limite (T3), Docker (T4), test separati (tutti), README e commit (ogni task).
- Il `CLAUDE.md` in radice resta non tracciato salvo tua richiesta; nel Task 4 viene modificato solo se lo versioni.
- Le versioni esatte delle dipendenze non sono note in anticipo: si fissano nel Task 1 da quelle installate.
