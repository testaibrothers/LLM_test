# Projekt: LLM-Debate Plattform (MVP)
# Mit Version-Switch zwischen Grundversion (vollständige Debatten-Engine) und Neu-Version (Prototyp)

import streamlit as st
import requests
import time
import json
import re

# === Hilfsfunktionen ===
def extract_json_fallback(text):
    optimistic = re.search(r'optimistic\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    pessimistic = re.search(r'pessimistic\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    recommendation = re.search(r'recommendation\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    return {
        "optimistic": optimistic.group(1).strip() if optimistic else "-",
        "pessimistic": pessimistic.group(1).strip() if pessimistic else "-",
        "recommendation": recommendation.group(1).strip() if recommendation else "-"
    }

def adjust_prompt_for_provider(prompt: str, provider: str) -> str:
    if "Groq" in provider:
        return (
            "Du bist ein präziser JSON-Antwortgenerator. Antworte nie mit Fließtext oder Code. "
            "Deine einzige Ausgabe ist folgendes JSON: "
            "{\"optimistic\":\"...\", \"pessimistic\":\"...\", \"recommendation\":\"...\"}. "
            "Gib kein Markdown, keine Einleitung, keine Erklärungen aus. Nur reines, minimales JSON.\n" + prompt
        )
    return prompt

# === API-Call mit Fallback ===
def debate_call(selected_provider, api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 200
    }
    while True:
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            st.error(f"Verbindungsfehler: {e}")
            return None, selected_provider

        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"], selected_provider
        if resp.status_code == 429:
            error = resp.json().get("error", {})
            if selected_provider.startswith("OpenAI") and error.get("code") == "insufficient_quota":
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

# === Debug-Fallback ===
def show_debug_output(raw):
    st.warning("Antwort nicht als JSON erkennbar. Roh-Antwort folgt:")
    st.code(raw, language="text")

# === Grundversion: Vollständige Debatten-Engine ===
def run_grundversion():
    st.title("🤖 KI-Debattenplattform – Grundversion")
    st.subheader("Single-Call Debatte mit Fallback & Live-Statistiken")

    provider = st.radio("Modell-Anbieter wählen:", ["OpenAI (gpt-3.5-turbo)", "Groq (Mistral-saba-24b)"])
    use_case = st.selectbox(
        "Use Case auswählen:",
        ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"],
        index=0
    )
    question = st.text_area("Deine Fragestellung:")
    start = st.button("Debatte starten")

    if start and question:
        progress = st.progress(0)
        st.info("Debatte läuft...")
        progress.progress(10)

        # Prompt-Aufbau
        if use_case == "Allgemeine Diskussion":
            base_prompt = (
                f"Thema: '{question}'\n"
                "Agent A (optimistisch)\nAgent B (pessimistisch)\n"
                "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
            )
        else:
            base_prompt = (
                f"Thema: '{question}'\n"
                "Agent A analysiert Chancen.\nAgent B analysiert Risiken.\n"
                "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
            )

        prompt = adjust_prompt_for_provider(base_prompt, provider)
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

        # API-Aufruf & Zeit messen
        start_time = time.time()
        content, used = debate_call(provider, api_key, api_url, model, prompt)
        duration = time.time() - start_time
        if not content:
            st.error("Keine Antwort erhalten.")
            progress.progress(100)
            return

        # Parsing
        raw = content.strip()
        if raw.startswith("```") and raw.endswith("```"):
            raw = "\n".join(raw.splitlines()[1:-1])

        if "{" in raw:
            try:
                data = json.loads(raw)
            except Exception:
                show_debug_output(raw)
                data = extract_json_fallback(raw)
        else:
            show_debug_output(raw)
            data = extract_json_fallback(raw)

        progress.progress(70)

        # Ausgabe & Stats
        st.markdown(f"**Provider:** {used}")
        if used.startswith("OpenAI"):
            tokens = len(raw.split())
            st.markdown(f"**Kosten:** ${(tokens/1000)*cost_rate:.4f}")
        st.markdown(f"**Dauer:** {duration:.2f}s")
        progress.progress(90)

        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))
        progress.progress(100)

# === Version Switch ===
version = st.selectbox("Version:", ["Grundversion"], index=0)
if version == "Grundversion":
    run_grundversion()
