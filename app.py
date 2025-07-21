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
use_case = st.selectbox("Use Case auswählen (Allgemeine Diskussion für freie Fragen):", ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"], index=0)
user_question = st.text_area("Deine Fragestellung:")
start_button = st.button("Debatte starten")

# Constants
timeout = 25

# Funktion: Ein API-Call und Fallback
def debate_call(selected_provider, api_key, api_url, model, prompt):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    resp = requests.post(api_url, headers=headers, json=payload)
    code = resp.status_code
    # Erfolgreicher Aufruf
    if code == 200:
        return resp.json()["choices"][0]["message"]["content"], selected_provider
    # Quota exceeded -> fallback zu Groq
    if code == 429 and selected_provider.startswith("OpenAI"):
        err = resp.json().get("error", {})
        if err.get("code") == "insufficient_quota":
            st.warning("OpenAI-Quota erschöpft, wechsle automatisch zu Groq...")
            gp = "Groq (Mistral-saba-24b)"
            key = st.secrets.get("groq_api_key", "")
            url = "https://api.groq.com/openai/v1/chat/completions"
            mdl = "mistral-saba-24b"
            time.sleep(timeout)
            return debate_call(gp, key, url, mdl, prompt)
    # Rate limit -> retry
    if code == 429:
        st.warning(f"Rate Limit bei {selected_provider}. Warte {timeout}s...")
        time.sleep(timeout)
        return debate_call(selected_provider, api_key, api_url, model, prompt)
    # Andere Fehler
    st.error(f"API-Fehler {code}: {resp.text}")
    return None, selected_provider

# Diskussion starten
if start_button and user_question:
    # Prompt-Erstellung basierend auf Use Case
    if use_case == "Allgemeine Diskussion":
        prompt = (
            f"Simuliere eine Debatte zwischen zwei KI-Agenten zum Thema: '{user_question}'
"
            "Agent A (optimistisch)
Agent B (pessimistisch)
"
            "Antworte ausschließlich mit einem JSON-Objekt mit den Feldern: optimistic, pessimistic, recommendation"
        )
    else:
        prompt = (
            f"Simuliere eine Debatte zwischen zwei KI-Agenten zum Use Case '{use_case}':
"
            f"Thema: '{user_question}'
"
            "Agent A (optimistisch) analysiert Chancen.
"
            "Agent B (pessimistisch) analysiert Risiken.
"
            "Antworte ausschließlich mit einem reinen JSON-Objekt ohne Code-Blöcke und ohne weiteren Text, verwende genau die Felder \"optimistic\", \"pessimistic\" und \"recommendation\""
        )
    # Provider konfigurieren
    if provider.startswith("OpenAI"):
        url = "https://api.openai.com/v1/chat/completions"
        key = st.secrets.get("openai_api_key", "")
        mdl = "gpt-3.5-turbo"
    else:
        url = "https://api.groq.com/openai/v1/chat/completions"
        key = st.secrets.get("groq_api_key", "")
        mdl = "mistral-saba-24b"

    # Call mit Fallback
    content, used = debate_call(provider, key, url, mdl, prompt)
    content, used = debate_call(provider, key, url, mdl, prompt)
    if content:
        try:
            data = json.loads(content)
            st.markdown(f"**Provider:** {used}")
            # 'debate'-Struktur
            if isinstance(data, dict) and 'debate' in data:
                st.markdown("### 🗣️ Debatte")
                for entry in data['debate']:
                    speaker = entry.get('speaker', 'Agent')
                    tone = entry.get('tone', '')
                    statement = entry.get('statement', '')
                    st.write(f"**{speaker}** ({tone}): {statement}")
                st.markdown("### ✅ Empfehlung")
                st.write(data.get('recommendation', '-'))
            # Legacy 'optimistic'/ 'pessimistic'
            elif isinstance(data, dict) and 'optimistic' in data and 'pessimistic' in data:
                st.markdown("### 🤝 Optimistische Perspektive")
                st.write(data.get('optimistic', '-'))
                st.markdown("### ⚠️ Pessimistische Perspektive")
                st.write(data.get('pessimistic', '-'))
                st.markdown("### ✅ Empfehlung")
                st.write(data.get('recommendation', '-'))
            # Key-based Agent A/B Format
            elif isinstance(data, dict) and any(k.startswith('Agent A') for k in data.keys()):
                st.markdown("### 🗣️ Debatte")
                for key, val in data.items():
                    if key.startswith('Agent A') or key.startswith('Agent B'):
                        tone = val.get('type', '')
                        message = val.get('message', '')
                        speaker_label = 'Agent A' if key.startswith('Agent A') else 'Agent B'
                        st.write(f"**{speaker_label}** ({tone}): {message}")
                st.markdown("### ✅ Empfehlung")
                rec = data.get('recommendation', {})
                rec_msg = rec.get('message') if isinstance(rec, dict) else rec
                st.write(rec_msg)
            else:
                st.error("Antwort konnte nicht geparst werden: " + content)
        except Exception as e:
            # Fallback: zeige die rohe Antwort, falls JSON-Parsing fehlschlägt
            st.warning("Antwort konnte nicht im JSON-Format geparst werden. Hier die Roh-Antwort:")
            st.text_area("Roh-Antwort", content, height=200)
    else:
        st.error("Keine Antwort erhalten.")
        st.error("Keine Antwort erhalten.")
