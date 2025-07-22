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
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        st.error(f"API-Fehler oder Verbindungsproblem: {e}")
        return None

# === Grundversion ===
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
        st.info("Debatte läuft...")
        if use_case == "Allgemeine Diskussion":
            prompt = (
                f"Thema: '{question}'\n"
                "Agent A (optimistisch)\nAgent B (pessimistisch)\n"
                "Bitte liefere ein JSON mit: optimistic, pessimistic, recommendation."
            )
        else:
            prompt = (
                f"Thema: '{question}'\n"
                "Agent A analysiert Chancen.\nAgent B analysiert Risiken.\n"
                "Bitte liefere ein JSON mit: optimistic, pessimistic, recommendation."
            )
        content = debate_call(st.secrets.get("openai_api_key", ""),
                              "https://api.openai.com/v1/chat/completions",
                              "gpt-3.5-turbo", prompt)
        if not content:
            st.error("Keine Antwort erhalten.")
            return
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = extract_json_fallback(content)
            show_debug_output(content)
        st.markdown(f"**Antwort:**")
        st.markdown("### 🤝 Optimistisch")
        st.write(data.get("optimistic", "-"))
        st.markdown("### ⚠️ Pessimistisch")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))

# === Neu-Version ===
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")
    st.info("Hinweis: Agent A startet immer die Diskussion basierend auf deinem Input.")

    # Texteingabe oder Datei
    text = st.text_area("Deine Idee/Businessplan/Thema:", height=150)
    upload = st.file_uploader("Oder Datei hochladen (PDF/TXT/DOCX):", type=["pdf","txt","docx"])
    if upload:
        # einfache Text-Parser (kein DOCX/PDF in dieser Version)
        try:
            text = upload.read().decode('utf-8')
            st.success("Datei eingelesen.")
        except:
            st.error("Fehler beim Einlesen der Datei.")

    col1, col2 = st.columns(2)
    model_a = col1.selectbox("Modell für Agent A", ["gpt-3.5-turbo","gpt-4"], key="neu_a")
    model_b = col2.selectbox("Modell für Agent B", ["gpt-3.5-turbo","gpt-4"], key="neu_b")

    mode = st.radio("Prompt-Modus",
                     ["Getrennter Prompt für B", "Gleicher Prompt für beide"])
    prompt_b = st.text_area("Prompt für Agent B:" if mode == "Getrennter Prompt für B" else "Gemeinsamer Prompt:",
                             height=100)

    if st.button("Diskussion starten"):
        if not text:
            st.error("Bitte Input eingeben oder Datei hochladen.")
            return
        api_key = st.secrets.get("openai_api_key", "")
        api_url = "https://api.openai.com/v1/chat/completions"
        resp_a = debate_call(api_key, api_url, model_a, text)
        resp_b = debate_call(api_key, api_url, model_b, prompt_b or text)
        st.markdown("### 🗣️ Antwort Agent A")
        st.write(resp_a or "Keine Antwort.")
        st.markdown("### 🗣️ Antwort Agent B")
        st.write(resp_b or "Keine Antwort.")

# Version-Auswahl
en
version = st.selectbox("Version:", ["Grundversion","Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
