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
        "max_tokens": 2000
    }
    resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"API-Fehler {resp.status_code}: {resp.text}")
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
    if st.button("Debatte starten") and question:
        progress = st.progress(0)
        st.info("Debatte läuft...")
        progress.progress(10)
        if use_case == "Allgemeine Diskussion":
            prompt = f"Thema: '{question}'\nAgent A (optimistisch)\nAgent B (pessimistisch)\nBitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
        else:
            prompt = f"Thema: '{question}'\nAgent A analysiert Chancen.\nAgent B analysiert Risiken.\nBitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
        progress.progress(30)
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        response = debate_call(api_key, api_url, "gpt-3.5-turbo", prompt)
        progress.progress(100)
        try:
            data = json.loads(response)
        except:
            data = extract_json_fallback(response)
            show_debug_output(response)
        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.markdown("###⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))

# === Neu-Version ===
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")

    # Sidebar: Prompt-Generator
    with st.sidebar.expander("🧠 Prompt-Generator", expanded=False):
        keyword = st.text_input("Schlagwort eingeben:", key="kw_gen")
        if st.button("Prompt generieren", key="gen_btn") and keyword:
            try:
                template = open("promptgen_header.txt", encoding="utf-8").read().strip()
                filled = template.replace("[SCHLAGWORT]", keyword)
                resp = debate_call(st.secrets.get("openai_api_key", ""), "https://api.openai.com/v1/chat/completions", "gpt-3.5-turbo", filled)
                filled = resp or "[Fehler bei der Generierung]"
            except FileNotFoundError:
                filled = f"[Promptdatei fehlt]\nSchlagwort: {keyword}"
            st.session_state["last_generated"] = filled
        st.text_area("Vorschlag:", value=st.session_state.get("last_generated", ""), height=100)
        c1, c2 = st.columns(2)
        if c1.button("In A übernehmen"):
            st.session_state["prompt_a"] = st.session_state.get("last_generated", "")
        if c2.button("In B übernehmen"):
            st.session_state["prompt_b"] = st.session_state.get("last_generated", "")

    # Hauptbereich
    idea = st.text_area("Deine Idee / Businessplan / Thema:")
    start_agent = st.radio("Welcher Agent soll starten?", ["Agent A", "Agent B"], key="start_agent")
    m_list = ["gpt-3.5-turbo", "gpt-4"]
    col1, col2 = st.columns(2)
    with col1:
        model_a = st.selectbox("Modell für Agent A", m_list, key="neu_a")
        prompt_a = st.text_area("Prompt für Agent A", st.session_state.get("prompt_a", ""), key="prompt_a")
    with col2:
        model_b = st.selectbox("Modell für Agent B", m_list, key="neu_b")
        prompt_b = st.text_area("Prompt für Agent B", st.session_state.get("prompt_b", ""), key="prompt_b")

    if st.button("Diskussion starten") and idea:
        api_key = st.secrets.get("openai_api_key", "")
        api_url = "https://api.openai.com/v1/chat/completions"
        prefix = f"Nutzeridee: {idea}\n"
        if start_agent == "Agent A":
            response = debate_call(api_key, api_url, model_a, prefix + prompt_a)
        else:
            response = debate_call(api_key, api_url, model_b, prefix + prompt_b)
        if response:
            st.markdown(f"### 🗣️ Antwort von {start_agent}")
            st.write(response)

    # Großes kosmetisches Ausgabefeld für finalen Konsens (ohne Logik)
    st.markdown("### 🏁 Finaler Konsens")
    st.text_area("Hier steht der finale Konsens:", value="", height=200)

version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
