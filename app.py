# Projekt: LLM-Debate Plattform (MVP)
# Ziel: Debatte in einem einzigen API-Call simulieren (optimistisch vs. pessimistisch + Empfehlung)

import streamlit as st
import requests
import json

# === STEP 1: UI + Konfiguration ===
st.title("🤖 KI-Debattenplattform (Single-Call)")
st.subheader("Simuliere optimistische und pessimistische Perspektiven in einem Aufruf")

provider = st.radio("Modell-Anbieter wählen:", ["OpenAI (gpt-3.5-turbo)", "Groq (Mistral-saba-24b)"])
use_case = st.selectbox("Use Case auswählen:", [
    "SaaS Validator",
    "SWOT Analyse",
    "Pitch-Kritik",
    "WLT Entscheidung"
])
user_question = st.text_area("Deine Fragestellung:")
start_button = st.button("Debatte starten")

# API-Endpunkte & Keys erst nach Klick abrufen
if start_button and user_question:
    if provider.startswith("OpenAI"):
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets["openai_api_key"]
        model = "gpt-3.5-turbo"
    else:
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        api_key = st.secrets.get("groq_api_key", "")
        model = "mistral-saba-24b"

    # Prompt für Single-Call-Debatte
    debate_prompt = (
        f"Simuliere eine Debatte zwischen zwei KI-Agenten zum Use Case '{use_case}':\n"
        "Agent A (optimistisch, lösungsorientiert, Chancen fokussiert)\n"
        "Agent B (pessimistisch, risikoorientiert, Gefahren fokussiert)\n"
        f"Thema: {user_question}\n"
        "Antworte im JSON-Format mit den Schlüsseln:\n"
        "optimistic, pessimistic, recommendation"
    )
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": debate_prompt}], "temperature": 0.7}

    # Single API Call
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code != 200:
        st.error(f"API-Fehler {response.status_code}: {response.text}")
    else:
        try:
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            st.markdown("### 🤝 Optimistische Perspektive")
            st.write(data.get("optimistic", "-"))
            st.markdown("### ⚠️ Pessimistische Perspektive")
            st.write(data.get("pessimistic", "-"))
            st.markdown("### ✅ Empfehlung")
            st.write(data.get("recommendation", "-"))
        except Exception:
            st.error("Antwort konnte nicht geparst werden: " + content)
