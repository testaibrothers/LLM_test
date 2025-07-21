# Projekt: LLM-Debate Plattform (MVP)
# Ziel: Single-Call Debatte mit automatischem Fallback bei OpenAI-Quota

import streamlit as st
import requests
import time
import json

# === UI + Konfiguration ===
st.title("🤖 KI-Debattenplattform (Auto-Fallback)")
st.subheader("Debattiere per JSON mit OpenAI oder Groq – wechsle bei Quotengrenze automatisch zu Groq")

provider = st.radio("Modell-Anbieter wählen:", ["OpenAI (gpt-3.5-turbo)", "Groq (Mistral-saba-24b)"])
use_case = st.selectbox("Use Case auswählen:", ["SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"])
user_question = st.text_area("Deine Fragestellung:")
start_button = st.button("Debatte starten")

# Constants
timeout = 25

# Funktion: Ein API-Call und Fallback
def debate_call(selected_provider, api_key, api_url, model, prompt):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    # Single call
    resp = requests.post(api_url, headers=headers, json=payload)
    code = resp.status_code
    if code == 200:
        return resp.json().get("choices")[0].get("message").get("content"), selected_provider
    # Quota exceeded -> fallback
    if code == 429 and selected_provider.startswith("OpenAI"):
        err = resp.json().get("error", {})
        if err.get("code") == "insufficient_quota":
            st.warning("OpenAI-Quota erschöpft, wechsle automatisch zu Groq...")
            # Setup Groq
            gp = "Groq (Mistral-saba-24b)"
            key = st.secrets.get("groq_api_key", "")
            url = "https://api.groq.com/openai/v1/chat/completions"
            mdl = "mistral-saba-24b"
            time.sleep(timeout)
            return debate_call(gp, key, url, mdl, prompt)
    # Rate limit generic
    if code == 429:
        st.warning(f"Rate Limit bei {selected_provider}. Warte {timeout}s...")
        time.sleep(timeout)
        return debate_call(selected_provider, api_key, api_url, model, prompt)
    # Other errors
    st.error(f"API-Fehler {code}: {resp.text}")
    return None, selected_provider

# Diskussion starten
if start_button and user_question:
    prompt = (
        f"Simuliere eine Debatte zwischen zwei KI-Agenten zum Use Case '{use_case}':\n"
        "Agent A (optimistisch)\nAgent B (pessimistisch)\n"
        f"Thema: {user_question}\nAntworte JSON mit: optimistic, pessimistic, recommendation"
    )

    # Initial provider setup
    if provider.startswith("OpenAI"):
        url = "https://api.openai.com/v1/chat/completions"
        key = st.secrets.get("openai_api_key", "")
        mdl = "gpt-3.5-turbo"
    else:
        url = "https://api.groq.com/openai/v1/chat/completions"
        key = st.secrets.get("groq_api_key", "")
        mdl = "mistral-saba-24b"

    # Call with fallback
    content, used = debate_call(provider, key, url, mdl, prompt)
    if content:
        try:
            data = json.loads(content)
            st.markdown(f"**Provider:** {used}")
            st.markdown("### 🤝 Optimistische Perspektive")
            st.write(data.get("optimistic", "-"))
            st.markdown("### ⚠️ Pessimistische Perspektive")
            st.write(data.get("pessimistic", "-"))
            st.markdown("### ✅ Empfehlung")
            st.write(data.get("recommendation", "-"))
        except Exception:
            st.error("Antwort konnte nicht geparst werden: " + content)
