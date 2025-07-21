# Projekt: LLM-Debate Plattform (MVP)
# Mit Version-Switch zwischen Grundversion (vollständige Debatten-Engine) und Neu-Version (Prototyp)

import streamlit as st
import requests
import time
import json

# === Funktion für Single-Call Debatte mit Fallback für OpenAI-Quota ===
def debate_call(selected_provider, api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    while True:
        resp = requests.post(api_url, headers=headers, json=payload)
        code = resp.status_code
        if code == 200:
            return resp.json()["choices"][0]["message"]["content"], selected_provider
        if code == 429 and selected_provider.startswith("OpenAI"):
            err = resp.json().get("error", {})
            if err.get("code") == "insufficient_quota":
                st.warning("OpenAI-Quota erschöpft, wechsle automatisch zu Groq...")
                return debate_call(
                    "Groq (Mistral-saba-24b)",
                    st.secrets.get("groq_api_key", ""),
                    "https://api.groq.com/openai/v1/chat/completions",
                    "mistral-saba-24b",
                    prompt,
                    timeout
                )
        if code == 429:
            st.warning(f"Rate Limit bei {selected_provider}. Warte {timeout}s...")
            time.sleep(timeout)
            continue
        st.error(f"API-Fehler {code}: {resp.text}")
        return None, selected_provider

# --- Grundversion: Vollständige Debatten-Engine ---
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
    start_btn = st.button("Debatte starten")

    if start_btn and question:
        progress = st.progress(0)
        st.info("Debatte läuft...")
        progress.progress(10)

        # Prompt-Aufbau
        if use_case == "Allgemeine Diskussion":
            prompt = (
                f"Simuliere eine Debatte zwischen zwei KI-Agenten zum Thema: '{question}'\n"
                "Agent A (optimistisch)\nAgent B (pessimistisch)\n"
                "Antwort als JSON mit Feldern: optimistic, pessimistic, recommendation"
            )
        else:
            prompt = (
                f"Simuliere Debatte zum Use Case '{use_case}': Thema: '{question}'\n"
                "Agent A analysiert Chancen.\nAgent B analysiert Risiken.\n"
                "Antwort als JSON: optimistic, pessimistic, recommendation"
            )
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

        # Call & Timing
        start_time = time.time()
        content, used = debate_call(provider, api_key, api_url, model, prompt)
        duration = time.time() - start_time
        if not content:
            st.error("Keine Antwort erhalten.")
            progress.progress(100)
            return

        # Preprocessing & Parsing
        raw = content.strip()
        if raw.startswith("```") and raw.endswith("```"):
            raw = "\n".join(raw.splitlines()[1:-1])
        try:
            data = json.loads(raw)
        except:
            st.warning("Antwort nicht JSON. Roh-Antwort:")
            st.text_area("Roh-Antwort", raw, height=200)
            progress.progress(100)
            return
        progress.progress(70)

        # Ausgabe & Stats
        st.markdown(f"**Provider:** {used}")
        if used.startswith("OpenAI"):
            tokens = len(raw.split())
            st.markdown(f"**Kosten:** ${(tokens/1000)*cost_rate:.4f}")
        st.markdown(f"**Dauer:** {duration:.2f}s")
        progress.progress(90)

        # JSON-Antwort anzeigen
        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get('optimistic', '-'))
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data.get('pessimistic', '-'))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get('recommendation', '-'))
        progress.progress(100)

# --- Neu-Version: erweiterter Prototyp ---
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")

    # Agenten-Modelle auswählen
    llm_list = ["gpt-3.5-turbo", "gpt-4", "claude-3", "mistral-7b", "llama-2-13b"]
    col1, col2 = st.columns(2)
    with col1:
        agent_a_model = st.selectbox("Agent A LLM:", llm_list, key="neu_a")
    with col2:
        agent_b_model = st.selectbox("Agent B LLM:", llm_list, key="neu_b")

    # Agent Konfiguration
    st.markdown("### Agent Konfiguration")
    mode = st.radio("Einstellung:", ["Prompt", "Charakter"], key="mode_neu")

    # Prompt-Konfiguration oder Charakter-Konfiguration
    if mode == "Prompt":    
        diff = st.checkbox("Different Prompts für A und B", key="diff_neu")
        if diff:
            prompt_a = st.text_area("Prompt für Agent A", placeholder="Je detaillierter der Prompt, desto besser das Ergebnis.", key="pA_neu")
            prompt_b = st.text_area("Prompt für Agent B", placeholder="Je detaillierter der Prompt, desto besser das Ergebnis.", key="pB_neu")
        else:
            shared = st.text_area("Gemeinsamer Prompt (optional)", placeholder="Je detaillierter der Prompt, desto besser das Ergebnis.", key="shared_same")
            prompt_a = shared
            prompt_b = shared
    else:
        opts = ["Optimistisch", "Pessimistisch", "Kritisch"]
        c1, c2 = st.columns(2)
                with c1:
            char_a = st.selectbox("Agent A:", opts, key="cA_neu")
        with c2:
            char_b = st.selectbox("Agent B:", opts, key="cB_neu")
        prompt_a = f"Du bist Agent A und agierst {char_a.lower()}."
        prompt_b = f"Du bist Agent B und agierst {char_b.lower()}."

    # Diskussion starten
    start_neu = st.button("Diskussion starten", key="start_neu")
    question_neu = st.text_area("Deine Frage:", key="q_neu")
    if start_neu and question_neu:
        st.markdown(f"**Modelle:** A={agent_a_model}, B={agent_b_model}")
        st.markdown(f"**Prompt A:** {prompt_a or '<leer>'}")
        st.markdown(f"**Prompt B:** {prompt_b or '<leer>'}")

# === Version Switch ===
version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
