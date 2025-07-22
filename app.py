# LLM-Debatte – Einfache Komplettversion in einer Datei (nur OpenAI)
import streamlit as st
import requests
import time
import json
import re

# === JSON Parsing ===
def extract_json_fallback(text):
    optimistic = re.search(r'optimistic\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    pessimistic = re.search(r'pessimistic\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    recommendation = re.search(r'recommendation\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    return {
        "optimistic": optimistic.group(1).strip() if optimistic else "-",
        "pessimistic": pessimistic.group(1).strip() if pessimistic else "-",
        "recommendation": recommendation.group(1).strip() if recommendation else "-"
    }

def show_debug_output(raw):
    st.warning("Antwort nicht als JSON erkennbar. Roh-Antwort folgt:")
    st.code(raw, language="text")

# === API Call ===
def debate_call(api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 200
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"API-Fehler {resp.status_code}: {resp.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

# === UI ===
def run_grundversion():
    st.title("🤖 KI-Debattenplattform – Grundversion")
    st.subheader("Single-Call Debatte mit OpenAI")

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

        if use_case == "Allgemeine Diskussion":
            prompt = (
                f"Thema: '{question}'\n"
                "Agent A (optimistisch)\nAgent B (pessimistisch)\n"
                "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
            )
        else:
            prompt = (
                f"Thema: '{question}'\n"
                "Agent A analysiert Chancen.\nAgent B analysiert Risiken.\n"
                "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
            )

        progress.progress(30)
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        model = "gpt-3.5-turbo"
        cost_rate = 0.002
        progress.progress(50)

        start_time = time.time()
        content = debate_call(api_key, api_url, model, prompt)
        duration = time.time() - start_time
        if not content:
            st.error("Keine Antwort erhalten.")
            progress.progress(100)
            return

        try:
            data = json.loads(content)
        except:
            data = extract_json_fallback(content)
            show_debug_output(content)

        st.markdown(f"**Dauer:** {duration:.2f}s")
        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.markdown("###⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))
        progress.progress(100)

# === Neu-Version ===
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")

    model_list = ["gpt-3.5-turbo", "gpt-4"]
    col1, col2 = st.columns(2)
    with col1:
        model_a = st.selectbox("Modell für Agent A", model_list, key="neu_a")
    with col2:
        model_b = st.selectbox("Modell für Agent B", model_list, key="neu_b")

    st.markdown("### Prompt-Modus")
    mode = st.radio("Eingabemodus", ["Getrennter Prompt für A und B", "Gleicher Prompt für beide"], key="modus")

    with st.sidebar.expander("🧠 Prompt-Generator", expanded=False):
        keyword = st.text_input("Schlagwort eingeben:", key="kw_gen")
        if st.button("Prompt generieren", key="gen_btn") and keyword:
            try:
                with open("promptgen_header.txt", "r", encoding="utf-8") as file:
                    template = file.read().strip()
                filled_prompt = template.replace("[SCHLAGWORT]", keyword)
                api_url = "https://api.openai.com/v1/chat/completions"
                api_key = st.secrets.get("openai_api_key", "")
                model = "gpt-3.5-turbo"
                response = debate_call(api_key, api_url, model, filled_prompt)
                if response:
                    filled_prompt = response
                else:
                    filled_prompt = "[Fehler bei der Generierung]"
            except FileNotFoundError:
                filled_prompt = f"[Promptdatei fehlt]\nSchlagwort: {keyword}"
            st.session_state["last_generated"] = filled_prompt
        st.text_area("Vorschlag:", value=st.session_state.get("last_generated", ""), height=100)
        cols = st.columns(2)
        with cols[0]:
            if st.button("In A übernehmen", key="toA"):
                st.session_state["prompt_a"] = st.session_state.get("last_generated", "")
        with cols[1]:
            if st.button("In B übernehmen", key="toB"):
                st.session_state["prompt_b"] = st.session_state.get("last_generated", "")

    if mode == "Getrennter Prompt für A und B":
        prompt_a = st.text_area("Prompt für Agent A", value=st.session_state.get("prompt_a", ""), key="prompt_a")
        prompt_b = st.text_area("Prompt für Agent B", value=st.session_state.get("prompt_b", ""), key="prompt_b")
    else:
        shared = st.text_area("Gleicher Prompt für beide", key="shared")
        prompt_a = prompt_b = shared

    start = st.button("Diskussion starten", key="start_neu")
    if start and (prompt_a and prompt_b):
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")

        response_a = debate_call(api_key, api_url, model_a, prompt_a)
        response_b = debate_call(api_key, api_url, model_b, prompt_b)

        st.markdown("### 🗣️ Antwort Agent A")
        st.write(response_a or "Keine Antwort")
        st.markdown("### 🗣️ Antwort Agent B")
        st.write(response_b or "Keine Antwort")

version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
