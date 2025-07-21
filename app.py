# Projekt: LLM-Debate Plattform (MVP)
# Ziel: Zwei LLMs diskutieren einen Use Case, liefern finalen Konsens mit Zusammenfassung

import openai
import streamlit as st

# === STEP 1: Konfiguration ===
openai.api_key = st.secrets["openai_api_key"]

MODEL_A = "gpt-4"
MODEL_B = "gpt-3.5-turbo"
MODEL_REF = "gpt-4"

MAX_ROUNDS = 4

USE_CASE_PROMPTS = {
    "SaaS Validator": "Bewerte die Idee kritisch unter folgenden Aspekten: Markt, Monetarisierung, Skalierung, Risiken.",
    "SWOT Analyse": "Erstelle gemeinsam eine SWOT-Analyse. Diskutiere gegensätzliche Positionen pro Faktor.",
    "Pitch-Kritik": "Analysiere den Pitch aus Sicht eines Investors. Was überzeugt, was fehlt, wo ist Risiko?",
    "WLT Entscheidung": "Welche Lösung ist langfristig tragfähiger? Diskutiere im Wechsel Argumente."
}

# === STEP 2: Streamlit UI ===
st.title("🤖 KI-Debattenplattform")
st.subheader("Zwei LLMs diskutieren für dich – bis zur Entscheidung")

use_case = st.selectbox("Use Case auswählen:", list(USE_CASE_PROMPTS.keys()))
user_question = st.text_area("Deine Fragestellung:")
start_button = st.button("Diskussion starten")

# === STEP 3: Agentenfunktion ===
def query_agent(model, history):
    response = openai.chat.completions.create(
        model=model,
        messages=history,
        temperature=0.7
    )
    return response.choices[0].message.content

# === STEP 4: Diskussion starten ===
if start_button and user_question:
    history_a = [
        {"role": "system", "content": f"Du bist ein KI-Agent, der die Aufgabe hat, folgende Fragestellung im Use Case '{use_case}' zu analysieren. {USE_CASE_PROMPTS[use_case]}"},
        {"role": "user", "content": user_question}
    ]

    history_b = [
        {"role": "system", "content": f"Du bist ein KI-Agent mit kritischem Blick. Reagiere auf die Aussagen des ersten Agenten zum Use Case '{use_case}'. {USE_CASE_PROMPTS[use_case]}"},
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
