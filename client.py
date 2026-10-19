"""Client minimo per il server locale di LM Studio.

Scheletro da completare con Claude Code (slide 19-22):
configurazione, messaggi, payload e chiamata HTTP.
Import e gestione degli errori sono gia' presenti: conservarli.
"""

import os

import requests
from dotenv import load_dotenv

# --- Configurazione -------------------------------------------------------
load_dotenv()
base_url = os.environ["LM_BASE_URL"]
model = os.environ["LM_MODEL"]

# --- Messaggi -------------------------------------------------------------
system = {"role": "system", "content": "Sei un assistente che risponde in italiano, in modo breve e chiaro."}
# Cronologia solo in memoria: si perde alla chiusura del programma.
messages = [system]

# --- Ciclo ----------------------------------------------------------------
# La cronologia completa viene inviata a ogni richiesta.
print("Scrivere una domanda ('esci' o Ctrl+C per terminare).")
try:
    while True:
        domanda = input("Tu: ").strip()
        if not domanda:
            continue
        if domanda.lower() == "esci":
            break

        # --- Payload ------------------------------------------------------
        # La domanda entra in messages solo se la richiesta riesce.
        user = {"role": "user", "content": domanda}
        payload = {
            "model": model,
            "messages": messages + [user],
            "temperature": 0.2,
            "max_tokens": 512,
            "reasoning_effort": "none",
            "stream": False,
        }

        # --- Chiamata -----------------------------------------------------
        try:
            response = requests.post(f"{base_url}/chat/completions", json=payload, timeout=60)
            response.raise_for_status()
            risposta = response.json()["choices"][0]["message"]["content"]
            messages.append(user)
            messages.append({"role": "assistant", "content": risposta})
            print(risposta)
        except requests.exceptions.Timeout:
            print("Attesa scaduta: controllare server, carico e tempi.")
        except requests.exceptions.ConnectionError:
            print("Connessione fallita: controllare server, URL e porta.")
        except requests.exceptions.HTTPError:
            print("Errore HTTP:", response.status_code, response.text)
except (KeyboardInterrupt, EOFError):
    print()
print("Arrivederci.")
