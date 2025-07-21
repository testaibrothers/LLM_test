# Projekt: LLM-Debate Plattform (MVP)
# Ziel: Single-Call Debatte mit automatischem Fallback und konfigurierbaren Agent-Profilen

import streamlit as st
import requests
import time
import json

# === UI + Konfiguration ===
st.title("🤖 KI-Debattenplattform (Auto-Fallback)")

# Use Case und Agent-Auswahl
use_case = st.selectbox(
    "Use Case auswählen:",
    ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"],
    index=0
)

# Agenten-Modelle auswählen (kosmetisch)
llm_list = [
    "gpt-3.5-turbo",
    "gpt-4",
    "claude-3",
    "mistral-7b",
    "llama-2-13b"
]
col1, col2 = st.columns(2)
with col1:
    agent_a_model = st.selectbox("Agent A LLM:", llm_list, index=0)
with col2:
    agent_b_model = st.selectbox("Agent B LLM:", llm_list, index=1)

# Nutzerinput
action = st.button("Debatte starten")
user_question = st.text_area("Deine Fragestellung:")

# === Funktion für API-Aufruf mit Fallback ===
action = st.button("Debatte starten")
user_question = st.text_area("Deine Fragestellung:")

# API-Call mit Fallback definieren
def debate_call(selected_provider, api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "system", "content": prompt}], "temperature": 0.7}
    while True:
        resp = requests.post(api_url, headers=headers, json=payload)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"], selected_provider
        if resp.status_code == 429:
            err = resp.json().get("error", {})
            if err.get("code") == "insufficient_quota" and selected_provider.startswith("OpenAI"):
                st.warning("OpenAI-Quota erschöpft, wechsle automatisch zu Groq...")
                return debate_call(
                    "Groq (Mistral-saba-24b)",
                    st.secrets.get("groq_api_key", ""),
                    "https://api.groq.com/openai/v1/chat/completions",
                    "mistral-saba-24b",
                    prompt,
                    timeout
                )
            st.warning(f"Rate Limit bei {selected_provider}. Warte {timeout}s...")
            time.sleep(timeout)
            continue
        st.error(f"API-Fehler {resp.status_code}: {resp.text}")
        return None, selected_provider

# Diskussion starten
if action and user_question:
    # Verhindere identische Profile
    if (a_tonality == b_tonality and a_risk == b_risk and a_focus == b_focus and a_style == b_style):
        st.error("Agent A und B dürfen nicht dieselben Profile haben.")
        st.stop()

    # Progress Bar und Zeitmessung
    progress = st.progress(0)
    progress.progress(10)
    start = time.time()

    # System-Prompt prefix
    system_prefix = (custom_system.strip() + "\n") if custom_system and custom_system.strip() else ""
    profile_a = f"Agent A Profil: Tonality={a_tonality}, Risikoprofil={a_risk}, Fokus={a_focus}, Analysestil={a_style}."
    profile_b = f"Agent B Profil: Tonality={b_tonality}, Risikoprofil={b_risk}, Fokus={b_focus}, Analysestil={b_style}."
    if use_case == "Allgemeine Diskussion":
        prompt = f"""{system_prefix}{profile_a}
{profile_b}
Simuliere eine Debatte zwischen zwei KI-Agenten zum Thema: '{user_question}'
Antworte ausschließlich mit einem JSON-Objekt mit den Feldern: optimistic, pessimistic, recommendation"""
    else:
        prompt = f"""{system_prefix}{profile_a}
{profile_b}
Simuliere eine Debatte zwischen zwei KI-Agenten zum Use Case '{use_case}':
Thema: '{user_question}'
Antworte ausschließlich mit einem reinen JSON-Objekt ohne Code-Blöcken und ohne weiteren Text, verwende genau die Felder \"optimistic\", \"pessimistic\" und \"recommendation\""""
    progress.progress(30)

    # Provider-Konfiguration
    if provider.startswith("OpenAI"):
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        model = "gpt-3.5-turbo"
        cost_rate = 0.002
    else:
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        api_key = st.secrets.get("groq_api_key", "")
        model = "mistral-saba-24b"
        cost_rate = 0.0
    progress.progress(50)

    content, used = debate_call(provider, api_key, api_url, model, prompt)
    duration = time.time() - start
    progress.progress(70)

    if not content:
        st.error("Keine Antwort erhalten.")
        st.stop()

    # Rohverarbeitung und Parsing
    raw = content.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.splitlines()[1:-1])
    try:
        data = json.loads(raw)
    except:
        st.warning("Antwort nicht im JSON-Format, roher Inhalt unten.")
        st.text_area("Roh-Antwort", raw, height=200)
        st.stop()
    progress.progress(90)

    # Ausgabe und Stats
    st.markdown(f"**Provider:** {used}")
    tokens = len(raw.split())
    if used.startswith("OpenAI"):
        st.markdown(f"**Geschätzte Kosten:** ${(tokens/1000)*cost_rate:.4f}")
    st.markdown(f"**Verarbeitungsdauer:** {duration:.2f} Sekunden")
    
    # Debattenausgabe
    if 'optimistic' in data and 'pessimistic' in data:
        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data['optimistic'])
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data['pessimistic'])
        st.markdown("### ✅ Empfehlung")
        st.write(data['recommendation'])
    else:
        st.warning("Unbekanntes Format, hier roher Inhalt:")
        st.text_area("Roh-Antwort", raw, height=200)
    progress.progress(100)
