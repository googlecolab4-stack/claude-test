# Assistente del laboratorio — specifica

Data: 2026-10-26 · Stato: **bozza in attesa di approvazione**

## Intento
Applicazione Python da terminale che conversa con un modello locale servito da LM Studio
tramite un grafo LangGraph esplicito. Il modello può chiedere uno strumento orologio; il
grafo lo esegue davvero, restituisce il risultato al modello e ottiene la risposta finale.
È la base didattica su cui le lezioni successive aggiungeranno altre funzioni.

## Obiettivi
- Ciclo di domande/risposte da terminale con cronologia in memoria per la durata della sessione.
- Grafo con stato, nodi e instradamento riconoscibili.
- Strumento `ora_corrente` con fuso orario esplicito, invocato tramite tool calling.
- Chiamate allo strumento visibili nei log; numero di passaggi del modello limitato.
- Avvio locale e con Docker Compose; LM Studio resta sull'host.
- Test automatici senza modello; istruzioni per prove reali (LM Studio e Docker).

## Non obiettivi
MCP, RAG, altri strumenti, workflow, interfacce grafiche o web, servizi cloud,
persistenza della cronologia, checkpointer LangGraph, streaming. Non si legge né si
modifica `lezione tre/` né altre lezioni.

## Anti-obiettivi
- Una risposta simulata presentata come prova che il modello locale usa lo strumento.
- Identificativo del modello inventato o scritto nel codice.
- Credenziali, `.env`, ambienti virtuali o cache in Git.

## Posizione
Il progetto vive nella **radice di `repo-lab-llm/`**; `lezione tre/` resta intatto.

## Architettura
Moduli piccoli, codice sincrono (pacchetto `assistente/`):

| Modulo | Responsabilità |
|---|---|
| `config.py` | Legge `LMSTUDIO_BASE_URL`, `LMSTUDIO_MODEL`, `MAX_PASSAGGI` (default 5) dall'ambiente. |
| `modello.py` | Crea `ChatOpenAI` (langchain-openai) verso LM Studio con gli strumenti collegati (`bind_tools`); interroga `GET /v1/models`. |
| `strumenti.py` | `ora_corrente(fuso_orario)`; l'istante è iniettabile per i test. |
| `grafo.py` | Stato, nodi, instradamento, limite di passaggi. |
| `cli.py` | Ciclo da terminale, cronologia, configurazione dei log. |

### Grafo
- **Stato:** `messaggi` (lista, riduttore `add_messages`) e `passaggi` (contatore dei turni del modello nella domanda corrente).
- **Nodi:** `modello` (invoca il modello, incrementa `passaggi`) e `strumenti` (esegue le richieste di strumento e produce `ToolMessage`).
- **Instradamento dopo `modello`:** se il messaggio ha richieste di strumento e `passaggi < MAX_PASSAGGI` → `strumenti`; se ha richieste ma il limite è raggiunto → fine con un messaggio esplicito di limite raggiunto; altrimenti → fine. Da `strumenti` si torna sempre a `modello`.
- Il contatore `passaggi` riparte da 0 a ogni domanda.
- Uno strumento sconosciuto o con argomenti errati produce un `ToolMessage` di errore, non un'eccezione.

### Strumento `ora_corrente`
- Parametro obbligatorio `fuso_orario`: nome IANA (es. `Europe/Rome`). Nessun valore predefinito.
- Usa `zoneinfo`; restituisce data e ora ISO 8601 con offset e il nome del fuso.
- Fuso non valido → testo di errore leggibile restituito al modello.
- Ogni esecuzione è registrata nei log (livello INFO) con nome e argomenti, e con esito.

### Cronologia
`cli.py` conserva la lista dei messaggi della sessione e la passa al grafo a ogni domanda,
sostituendola con lo stato finale. Nessuna persistenza: chiusa la sessione, la cronologia è persa.
Comando `exit` / Ctrl+D per uscire.

### Configurazione
- Solo variabili d'ambiente. `LMSTUDIO_BASE_URL` obbligatoria (nessun default nel codice;
  `.env.example` riporta `http://localhost:1234/v1`, in Docker `http://host.docker.internal:1234/v1`).
- `LMSTUDIO_MODEL` opzionale: se assente l'app interroga `/v1/models`, mostra gli identificativi
  e termina chiedendo di impostarla (non ne sceglie uno da sola). Se impostata ma non presente
  nell'elenco, errore chiaro con l'elenco.
- Chiave API: LM Studio non la richiede; si passa un segnaposto fisso richiesto dal client, non configurabile.
- `.env.example` senza credenziali; `.env` in `.gitignore`.
- Errori di connessione a LM Studio → messaggio comprensibile, non traceback.

## Dipendenze (versioni fissate in `requirements.txt`)
- `langgraph`, `langchain-openai` (e `langchain-core` come transitiva): richiesti dal grafo e dal collegamento al modello.
- `pytest` (in `requirements-dev.txt`): test.
- `tzdata`: database dei fusi su Windows e nell'immagine slim.
Le versioni esatte vengono verificate e fissate nel piano.

## Test
- **Automatici (pytest, nessun modello):** modello finto con risposte scritte a mano per verificare:
  instradamento (con/senza strumento), ciclo strumento→modello→risposta, limite di passaggi,
  cronologia tra due domande, gestione strumento/argomenti errati, `ora_corrente` con istante
  fisso e fuso non valido, configurazione (variabili mancanti, modello assente dall'elenco).
- **Prove reali (esplicite, separate):** marcatore pytest `reale` escluso di default, attivato con
  `pytest -m reale`; verifica che `gemma-4-e2b` richieda davvero lo strumento. Documentate anche la
  prova manuale da terminale e la prova con Docker Compose. L'esito della prova reale può essere negativo
  (modello piccolo): in tal caso va riportato, non mascherato.
- Il resoconto di ogni incremento dice cosa è stato eseguito, con quale esito e cosa resta da provare.

## Docker
`Dockerfile` (Python slim, installa `requirements.txt`, utente non root) e `compose.yaml` con un
servizio `assistente`: `stdin_open`/`tty`, variabili da `.env`, `LMSTUDIO_BASE_URL` verso
`host.docker.internal` (con `extra_hosts: host.docker.internal:host-gateway` per portabilità).
Avvio: `docker compose run --rm assistente`. LM Studio non è containerizzato; deve accettare
connessioni dal server locale (porta 1234).

## Log
Modulo `logging` standard su stderr; livello da `LOG_LEVEL` (default INFO). Registrati: richiesta
di strumento (nome, argomenti), risultato, passaggio e raggiungimento del limite.

## Documentazione e Git
README con configurazione, avvio, test, diagnosi e comandi PowerShell, solo comandi verificati.
Commit in italiano (Conventional Commits), incrementi piccoli, nessun push senza richiesta.

## Chiarimenti dopo la revisione
- **Posizione (deciso dall'utente):** pacchetto, `tests/`, `Dockerfile`, `compose.yaml`, `.gitignore`,
  `.env.example`, `requirements*.txt` e `README.md` stanno nella radice di `repo-lab-llm/`. `lezione tre/`
  (codice di una lezione precedente) non si legge, non si modifica e non si rimuove; il suo `.gitignore`
  e i suoi file non influiscono sul nuovo progetto. Il `CLAUDE.md` valido è quello in `repo-lab-llm/`.
- **Prova reale:** il test `reale` legge `LMSTUDIO_MODEL` e `LMSTUDIO_BASE_URL` dall'ambiente e viene
  saltato se mancano. `gemma-4-e2b` compare solo nella documentazione come modello usato nella prova.
- **Limite raggiunto:** il nodo finale aggiunge un messaggio assistente di limite e sostituisce l'ultimo
  messaggio del modello con una versione priva di richieste di strumento, così la cronologia resta valida
  per la domanda successiva (con test).
- **Più strumenti in una risposta:** `strumenti` esegue tutte le richieste, un `ToolMessage` ciascuna;
  `passaggi` conta solo i turni del modello.
- **Prompt di sistema:** aggiunto dal nodo `modello` a ogni invocazione, non salvato nella cronologia.
- **Errori di connessione:** la CLI stampa il messaggio, scarta la domanda fallita e la sessione continua;
  all'avvio, se l'elenco modelli non è raggiungibile, esce con codice diverso da zero.
- **Python:** 3.11 (versione locale verificata) per ambiente locale e immagine `python:3.11-slim`.
  `LOG_LEVEL` è letto in `cli.py`.

## Scelte mie (da confermare)
- Limite predefinito di 5 passaggi, configurabile con `MAX_PASSAGGI`.
- Pacchetto `assistente/`, test in `tests/`, nomi dei moduli in italiano.
- Output del limite raggiunto come messaggio assistente leggibile.
- Lingua: prompt di sistema breve in italiano che invita a usare lo strumento per l'ora.
