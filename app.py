# Projekt: LLM-Debate Plattform (MVP)
# Mit Version-Switch zwischen Grundversion (vollständige Debatten-Engine) und Neu-Version (Prototyp)

import streamlit as st
import requests
import time
import json

# === API-Call mit Fallback ===
def debate_call(selected_provider, api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "system", "content": prompt}], "temperature": 0.7}
    while True:
        resp = requests.post(api_url, headers=headers, json=payload)
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

        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))
        progress.progress(100)

# === Neu-Version: Prototyp mit Prompt- und Charakter-Einstellungen ===
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")

    # Agentenauswahl
    llm_list = ["gpt-3.5-turbo", "gpt-4", "claude-3", "mistral-saba-24b", "llama-2-13b"]
    col1, col2 = st.columns(2)
    with col1:
        agent_a_model = st.selectbox("Agent A LLM:", llm_list, key="neu_a")
    with col2:
        agent_b_model = st.selectbox("Agent B LLM:", llm_list, key="neu_b")

    # Agenteinstellung
    st.markdown("### Agenteinstellung")
    mode = st.radio("Einstellung:", ["Prompt", "Charakter"], key="mode_neu")

        # Prompt-Konfiguration
    if mode == "Prompt":
        # Prompt-Generator als optionales Sidebar-Feature
        with st.sidebar.expander("Prompt-Generator (optional)", expanded=False):
            st.markdown("Verwende ein Schlagwort, um einen professionellen Prompt zu generieren:")
            keyword = st.text_input("Schlagwort:", key="gen_kw")
            if st.button("Generiere Prompt", key="gen_btn") and keyword:
                init_sys = (
                    "Du bist ein professioneller Prompt-Designer auf Expertenniveau, spezialisiert auf die Entwicklung effizienter, "
                    "präziser und anwendungsoptimierter Prompts. Deine Aufgabe ist es, in einem Gespräch mit mir Prompts für andere "
                    "LLM-Instanzen zu entwickeln."
                )
                generator_url = "https://api.groq.com/openai/v1/chat/completions"
                generator_key = st.secrets.get("groq_api_key", "")
                # Schritt 1: System-Kontext initialisieren
                _, _ = debate_call(
                    "Groq",
                    generator_key,
                    generator_url,
                    "mistral-saba-24b",
                    init_sys
                )
                # Schritt 2: Generierung basierend auf dem Schlagwort
                prompt_gen, _ = debate_call(
                    "Groq",
                    generator_key,
                    generator_url,
                    "mistral-saba-24b",
                    keyword
                )
                # Ausgabe des generierten Prompts
                st.text_area(
                    "Generierter Prompt:",
                    prompt_gen or "Fehler bei der Prompt-Generierung",
                    height=150,
                    key="gen_out"
                )
        # Agent-Prompts
        diff = st.checkbox("Unterschiedliche Prompts für A und B", key="diff_neu")
        if diff:
            prompt_a = st.text_area("Prompt für Agent A", placeholder="Je detaillierter..., desto besser.", key="pA_neu")
            prompt_b = st.text_area("Prompt für Agent B", placeholder="Je detaillierter..., desto besser.", key="pB_neu")
        else:
            shared = st.text_area("Gemeinsamer Prompt (optional)", placeholder="Je detaillierter..., desto besser.", key="shared_same")
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

    # Diskussion starten & Ausführen
    question_neu = st.text_area("Deine Frage:", key="q_neu")
    if st.button("Diskussion starten", key="start_neu") and question_neu:
        st.markdown(f"**Modelle:** A={agent_a_model}, B={agent_b_model}")
        combined_a = prompt_a + "\n" + question_neu
        combined_b = prompt_b + "\n" + question_neu
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        resp_a, _ = debate_call("OpenAI", api_key, api_url, agent_a_model, combined_a)
        resp_b, _ = debate_call("OpenAI", api_key, api_url, agent_b_model, combined_b)
        st.markdown("### 🗣️ Agent A Antwort")
        st.write(resp_a)
        st.markdown("### 🗣️ Agent B Antwort")
        st.write(resp_b)

# === Version Switch ===
version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
