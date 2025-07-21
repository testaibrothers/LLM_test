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
use_case = st.selectbox(
    "Use Case auswählen:",
    ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"],
    index=0
)
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
            return debate_call(
                "Groq (Mistral-saba-24b)",
                st.secrets.get("groq_api_key", ""),
                "https://api.groq.com/openai/v1/chat/completions",
                "mistral-saba-24b",
                prompt
            )
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
    progress = st.progress(0)
    st.info("Debatte läuft...")
    progress.progress(5)
    # Prompt-Erstellung basierend auf Use Case
    if use_case == "Allgemeine Diskussion":
        prompt = f"""Simuliere eine Debatte zwischen zwei KI-Agenten zum Thema: '{user_question}'\nAgent A (optimistisch)\nAgent B (pessimistisch)\nAntworte ausschließlich mit einem JSON-Objekt mit den Feldern: optimistic, pessimistic, recommendation"""
    else:
        prompt = f"""Simuliere eine Debatte zwischen zwei KI-Agenten zum Use Case '{use_case}':\nThema: '{user_question}'\nAgent A (optimistisch) analysiert Chancen.\nAgent B (pessimistisch) analysiert Risiken.\nAntworte ausschließlich mit einem reinen JSON-Objekt ohne Code-Blöcke und ohne weiteren Text, verwende genau die Felder \"optimistic\", \"pessimistic\" und \"recommendation\""""
    # Provider konfigurieren
    if provider.startswith("OpenAI"):
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        model = "gpt-3.5-turbo"
    else:
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        api_key = st.secrets.get("groq_api_key", "")
        model = "mistral-saba-24b"

    # Call mit Fallback
    content, used = debate_call(provider, api_key, api_url, model, prompt)
    if content:
        try:
            # Vor Parsing: Entferne Markdown-Fences
            raw = content.strip()
            if raw.startswith("```") and raw.endswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(lines[1:-1])
            data = json.loads(raw)
            st.markdown(f"**Provider:** {used}")
            progress.progress(20)
            # API-Kosten schätzen (nur OpenAI)
            try:
                # Roh-Antwort befindet sich in raw
                tokens = len(raw.split())
                est_cost = tokens/1000 * cost_rate
                st.markdown(f"**Geschätzte Kosten:** ${est_cost:.4f}")
            except Exception:
                pass
            progress.progress(40)
            # Legacy optimistic/pessimistic JSON
            if 'optimistic' in data and 'pessimistic' in data:
                st.markdown("### 🤝 Optimistische Perspektive")
                st.write(data['optimistic'])
                st.markdown("### ⚠️ Pessimistische Perspektive")
                st.write(data['pessimistic'])
                st.markdown("### ✅ Empfehlung")
                st.write(data['recommendation'])
            # Key-based Agent A/B Format
            elif any(key.startswith('Agent A') or key.startswith('Agent B') for key in data.keys()):
                st.markdown("### 🗣️ Debatte")
                for key, val in data.items():
                    if key.startswith('Agent A') or key.startswith('Agent B'):
                        tone = val.get('type', '')
                        message = val.get('message', '')
                        speaker = 'Agent A' if 'A' in key else 'Agent B'
                        st.write(f"**{speaker}** ({tone}): {message}")
                st.markdown("### ✅ Empfehlung")
                rec = data.get('recommendation', {})
                st.write(rec.get('message') if isinstance(rec, dict) else rec)
            else:
                # Fallback: zeige Roh-Antwort
                st.warning("Unbekanntes JSON-Format, hier Roh-Antwort:")
                st.text_area("Roh-Antwort", content, height=200)            progress.progress(100)
        except Exception as e:
            st.error("Fehler beim Verarbeiten der Antwort: " + str(e))
    else:
        st.error("Keine Antwort erhalten.")
