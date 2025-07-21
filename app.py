# Projekt: LLM-Debate Plattform (MVP)
# Ziel: Zwei LLMs diskutieren einen Use Case, liefern finalen Konsens mit Zusammenfassung

import streamlit as st
import requests
import time
import os

# === STEP 1: Konfiguration ===
st.title("🤖 KI-Debattenplattform")
st.subheader("Zwei LLMs diskutieren für dich – bis zur Entscheidung")

provider = st.radio("Modell-Anbieter wählen:", ["Groq (Mixtral)", "OpenAI (gpt-3.5)"])

USE_GROQ = provider.startswith("Groq")

if USE_GROQ:
    API_KEY = st.secrets["groq_api_key"]
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_A = MODEL_B = MODEL_REF = "mixtral-8x7b"
else:
    import openai
    API_KEY = st.secrets["openai_api_key"]
    API_URL = "https://api.openai.com/v1/chat/completions"
    MODEL_A = MODEL_B = MODEL_REF = "gpt-3.5-turbo"

MAX_ROUNDS = 4
WAIT_BETWEEN_CALLS = 25

USE_CASE_PROMPTS = {
    "SaaS Validator": "Bewerte die Idee kritisch unter folgenden Aspekten: Markt, Monetarisierung, Skalierung, Risiken.",
    "SWOT Analyse": "Erstelle gemeinsam eine SWOT-Analyse. Diskutiere gegensätzliche Positionen pro Faktor.",
    "Pitch-Kritik": "Analysiere den Pitch aus Sicht eines Investors. Was überzeugt, was fehlt, wo ist Risiko?",
    "WLT Entscheidung": "Welche Lösung ist langfristig tragfähiger? Diskutiere im Wechsel Argumente."
}

# === STEP 2: Streamlit UI ===
use_case = st.selectbox("Use Case auswählen:", list(USE_CASE_PROMPTS.keys()))
user_question = st.text_area("Deine Fragestellung:")
start_button = st.button("Diskussion starten")

# === STEP 3: Agentenfunktion ===
def query_agent(model, history):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": history,
        "temperature": 0.7
    }
    while True:
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                st.warning(f"Rate Limit bei {model}. Warte {WAIT_BETWEEN_CALLS} Sekunden…")
                time.sleep(WAIT_BETWEEN_CALLS)
            else:
                st.error(f"Fehler von API ({response.status_code}): {response.text}")
                return "[Fehler bei API-Zugriff]"
        except Exception as e:
            st.error(f"Verbindungsfehler: {str(e)}")
            time.sleep(WAIT_BETWEEN_CALLS)

# === STEP 4: Diskussion starten ===
if start_button and user_question:
    history_a = [
        {"role": "system", "content": f"Du bist ein optimistisch eingestellter KI-Agent, der die Aufgabe hat, folgende Fragestellung im Use Case '{use_case}' wohlwollend, lösungsorientiert und chancenfokussiert zu analysieren. {USE_CASE_PROMPTS[use_case]}"},
        {"role": "user", "content": user_question}
    ]

    history_b = [
        {"role": "system", "content": f"Du bist ein eher pessimistisch eingestellter KI-Agent mit kritischem Blick. Reagiere mit Skepsis auf die Aussagen des ersten Agenten und fokussiere dich auf Risiken, Schwächen und potenzielle Fehlschläge im Use Case '{use_case}'. {USE_CASE_PROMPTS[use_case]}"},
        {"role": "user", "content": user_question}
    ]

    st.info("💬 Diskussion läuft...")
    for round in range(MAX_ROUNDS):
        msg_a = query_agent(MODEL_A, history_a)
        history_b.append({"role": "assistant", "content": msg_a})
        history_a.append({"role": "assistant", "content": msg_a})

        msg_b = query_agent(MODEL_B, history_b)
        history_a.append({"role": "assistant", "content": msg_b})
        history_b.append({"role": "assistant", "content": msg_b})

    # === STEP 5: Konsensfindung ===
    referee_prompt = f"Zwei Agenten haben über die Frage diskutiert: '{user_question}' im Kontext '{use_case}'. Fasse ihre Kernaussagen zusammen, identifiziere Übereinstimmungen, bestes Argument und gib eine klare Empfehlung."
    history_ref = [
        {"role": "system", "content": referee_prompt},
        {"role": "user", "content": "Hier ist der Diskussionsverlauf:\n" + str(history_a)}
    ]

    final_summary = query_agent(MODEL_REF, history_ref)

    st.success("✅ Diskussion abgeschlossen")
    st.markdown("### 🧠 Ergebnis")
    st.markdown(final_summary)
