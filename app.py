# LLM-Debatte – Einfache Komplettversion in einer Datei (nur OpenAI)
import streamlit as st
import requests
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
    try:
        resp = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "system", "content": prompt}], "temperature": 0.2, "max_tokens": 200},
            timeout=timeout
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"API-Fehler oder Verbindungsproblem: {e}")
        return None

# === Grundversion ===
def run_grundversion():
    st.title("🤖 KI-Debattenplattform – Grundversion")
    st.subheader("Single-Call Debatte mit OpenAI")
    use_case = st.selectbox(
        "Use Case auswählen:",
        ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"]
    )
    question = st.text_area("Deine Fragestellung:")
    if st.button("Debatte starten") and question:
        prompt = (
            f"Thema: '{question}'\n"
            + ("Agent A (optimistisch)\nAgent B (pessimistisch)\n" if use_case == "Allgemeine Diskussion" else "Agent A analysiert Chancen.\nAgent B analysiert Risiken.\n")
            + "Bitte liefere ein JSON mit: optimistic, pessimistic, recommendation."
        )
        content = debate_call(
            st.secrets.get("openai_api_key", ""),
            "https://api.openai.com/v1/chat/completions",
            "gpt-3.5-turbo",
            prompt
        )
        if not content:
            st.error("Keine Antwort erhalten.")
            return
        try:
            data = json.loads(content)
        except:
            data = extract_json_fallback(content)
            show_debug_output(content)
        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))

# === Neu-Version ===
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")
    st.sidebar.title("🧠 Prompt-Generator")
    with st.sidebar.expander("Generator", expanded=False):
        keyword = st.text_input("Schlagwort eingeben:")
        if st.button("Prompt generieren") and keyword:
            try:
                template = open("promptgen_header.txt", encoding="utf-8").read()
                filled = template.replace("[SCHLAGWORT]", keyword)
                gen = debate_call(st.secrets.get("openai_api_key", ""), "https://api.openai.com/v1/chat/completions", "gpt-3.5-turbo", filled)
                st.session_state["last_generated"] = gen or "[Fehler]"
            except:
                st.session_state["last_generated"] = "[Datei fehlt]"
        st.text_area("Vorschlag:", value=st.session_state.get("last_generated", ""), height=120)
        c1, c2 = st.columns(2)
        if c1.button("In A übernehmen"): st.session_state["prompt_a"] = st.session_state.get("last_generated", "")
        if c2.button("In B übernehmen"): st.session_state["prompt_b"] = st.session_state.get("last_generated", "")

    text = st.text_area("Deine Idee/Businessplan/Thema:", height=150)
    uploaded = st.file_uploader("Oder Datei hochladen:", type=["pdf","txt","docx"])
    if uploaded:
        try: text = uploaded.read().decode('utf-8'); st.success("Datei eingelesen.")
        except: st.error("Fehler beim Einlesen.")

    c1, c2 = st.columns(2)
    model_a = c1.selectbox("Modell für Agent A", ["gpt-3.5-turbo","gpt-4"], key="neu_a")
    model_b = c2.selectbox("Modell für Agent B", ["gpt-3.5-turbo","gpt-4"], key="neu_b")
    # Wer startet? Kreis-Auswahl ohne Label
    starter = st.radio("", ["A", "B"], horizontal=True)

    if starter == "A": prompt_a = text; prompt_b = st.text_area("Prompt für Agent B:", height=100, key="prompt_b")
    else: shared = st.text_area("Gemeinsamer Prompt:", height=100, key="shared"); prompt_a = prompt_b = shared

    if st.button("Diskussion starten"):
        if not text:
            st.error("Bitte Input oder Datei.")
            return
        key = st.secrets.get("openai_api_key", "")
        url = "https://api.openai.com/v1/chat/completions"
        resp_a = debate_call(key, url, model_a, prompt_a)
        resp_b = debate_call(key, url, model_b, prompt_b)
        st.markdown("### 🗣️ Antwort Agent A")
        st.write(resp_a or "Keine Antwort.")
        st.markdown("### 🗣️ Antwort Agent B")
        st.write(resp_b or "Keine Antwort.")

# Version-Auswahl
version = st.selectbox("Version:", ["Grundversion","Neu-Version"])
if version == "Grundversion": run_grundversion()
else: run_neu()
