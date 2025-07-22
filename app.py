# LLM-Debatte – Einfache Komplettversion in einer Datei (nur OpenAI)
import streamlit as st
import requests
import json
import re
import time

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

# === API Call ===
def debate_call(api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "system", "content": prompt}], "temperature": 0.2, "max_tokens": 200}
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
    if st.button("Debatte starten") and question:
        progress = st.progress(0)
        st.info("Debatte läuft...")
        progress.progress(10)
        if use_case == "Allgemeine Diskussion":
            prompt = f"Thema: '{question}'\nAgent A (optimistisch)\nAgent B (pessimistisch)\nBitte liefere als Ergebnis ein JSON mit: optimistic, pessimistic, recommendation."
        else:
            prompt = f"Thema: '{question}'\nAgent A analysiert Chancen.\nAgent B analysiert Risiken.\nBitte liefere als Ergebnis ein JSON mit: optimistic, pessimistic, recommendation."
        progress.progress(30)
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        result = debate_call(api_key, api_url, "gpt-3.5-turbo", prompt)
        progress.progress(100)
        try:
            data = json.loads(result)
        except:
            data = extract_json_fallback(result)
            st.warning("Antwort nicht als JSON erkennbar. Roh-Antwort folgt:")
            st.code(result, language="text")
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
        keyword = st.text_input("Schlagwort eingeben:")
        if st.button("Prompt generieren") and keyword:
            try:
                with open("promptgen_header.txt", "r", encoding="utf-8") as f:
                    template = f.read().strip()
                gen_prompt = template.replace("[SCHLAGWORT]", keyword)
                gen_resp = debate_call(st.secrets.get("openai_api_key", ""), "https://api.openai.com/v1/chat/completions", "gpt-3.5-turbo", gen_prompt)
                st.session_state["prompt_a"] = gen_resp or ""
                st.session_state["prompt_b"] = gen_resp or ""
            except FileNotFoundError:
                st.session_state["prompt_a"] = ""
                st.session_state["prompt_b"] = ""
        st.text_area("Vorschlag", st.session_state.get("prompt_a", ""), height=100)

    # Hauptbereich
    idea = st.text_area("Deine Idee / Businessplan / Thema:")
    start_agent = st.radio("Welcher Agent startet?", ["Agent A", "Agent B"], horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        model_a = st.selectbox("Modell Agent A", ["gpt-3.5-turbo", "gpt-4"], key="neu_a")
        prompt_a = st.text_area("Prompt Agent A", st.session_state.get("prompt_a", ""), height=120)
    with col2:
        model_b = st.selectbox("Modell Agent B", ["gpt-3.5-turbo", "gpt-4"], key="neu_b")
        prompt_b = st.text_area("Prompt Agent B", st.session_state.get("prompt_b", ""), height=120)

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

version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
