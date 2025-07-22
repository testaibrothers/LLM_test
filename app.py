# LLM-Debatte – Professionell überarbeitete Version
import streamlit as st
import requests
import json
import re

def extract_json_fallback(text):
    optimistic = re.search(r'optimistic\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    pessimistic = re.search(r'pessimistic\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    recommendation = re.search(r'recommendation\W+(.*?)\n', text, re.IGNORECASE | re.DOTALL)
    return {
        "optimistic": optimistic.group(1).strip() if optimistic else "-",
        "pessimistic": pessimistic.group(1).strip() if pessimistic else "-",
        "recommendation": recommendation.group(1).strip() if recommendation else "-"
    }

def debate_call(api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "system", "content": prompt}], "temperature": 0.2, "max_tokens": 2000}
    response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    st.error(f"API-Fehler {response.status_code}")
    return None

# === Layout ===
st.set_page_config(page_title="KI-Debattenplattform", layout="wide")
st.markdown("<div style='text-align:center;'><h1>KI-Debattenplattform</h1><p style='color:gray;'>Professionelle Diskussion mit mehreren Agenten</p></div>", unsafe_allow_html=True)
st.divider()

# Auswahl Version
def sidebar_settings():
    version = st.sidebar.selectbox("Version wählen", ["Grundversion", "Neu-Version"], index=1)
    return version

version = sidebar_settings()

# === Grundversion ===
def run_grundversion():
    st.header("Grundversion")
    use_case = st.selectbox("Use Case", ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"])
    question = st.text_area("Fragestellung", height=150)
    if st.button("Start"):  
        with st.spinner("Debatte läuft…"):
            if use_case == "Allgemeine Diskussion":
                prompt = f"Thema: '{question}'\nAgent A (optimistisch)\nAgent B (pessimistisch)\nBitte JSON mit: optimistic, pessimistic, recommendation."
            else:
                prompt = f"Thema: '{question}'\nAgent A analysiert Chancen.\nAgent B analysiert Risiken.\nBitte JSON mit: optimistic, pessimistic, recommendation."
            result = debate_call(st.secrets.get("openai_api_key"), "https://api.openai.com/v1/chat/completions", "gpt-3.5-turbo", prompt)
            try:
                data = json.loads(result)
            except:
                data = extract_json_fallback(result)

        st.subheader("Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.subheader("Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.subheader("Empfehlung")
        st.write(data.get("recommendation", "-"))

# === Neu-Version ===
def run_neu():
    st.header("Neu-Version")
    with st.sidebar.expander("Prompt-Generator", expanded=False):
        keyword = st.text_input("Schlagwort")
        if st.button("Generieren"):
            template = "[SCHLAGWORT] analysieren: Chancen & Risiken"
            filled = template.replace("[SCHLAGWORT]", keyword)
            gen = debate_call(st.secrets.get("openai_api_key"), "https://api.openai.com/v1/chat/completions", "gpt-3.5-turbo", filled)
            st.session_state.last_generated = gen or "Fehler"
        st.text_area("Vorschlag", st.session_state.get("last_generated", ""), height=120)
        c1, c2 = st.columns(2)
        if c1.button("In A übernehmen"): st.session_state.prompt_a = st.session_state.get("last_generated", "")
        if c2.button("In B übernehmen"): st.session_state.prompt_b = st.session_state.get("last_generated", "")

    col1, col2 = st.columns([2,1])
    with col1:
        idea = st.text_area("Idee / Businessplan / Thema", height=120)
        st.radio("Startender Agent", ["Agent A", "Agent B"], key="start_agent", horizontal=True)
        st.text_area("Finaler Konsens (kosmetisch)", value="", height=150)
    with col2:
        st.subheader("Modelle & Prompts")
        m_list = ["gpt-3.5-turbo", "gpt-4"]
        st.selectbox("Modell Agent A", m_list, key="neu_a")
        st.text_area("Prompt Agent A", st.session_state.get("prompt_a", ""), height=120)
        st.selectbox("Modell Agent B", m_list, key="neu_b")
        st.text_area("Prompt Agent B", st.session_state.get("prompt_b", ""), height=120)
        st.button("Diskussion starten")

if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
