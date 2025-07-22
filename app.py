# LLM-Debatte – Einfache Komplettversion in einer Datei (nur OpenAI)
import streamlit as st
import requests
import time
import json
import re

# Zusätzliche Bibliotheken für Datei-Parsing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None

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

# Helfer: Datei-Inhalt extrahieren
def parse_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    data = ""
    try:
        if name.endswith('.txt'):
            data = uploaded_file.read().decode('utf-8')
        elif name.endswith('.pdf') and PyPDF2:
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                data += (page.extract_text() or '') + '\n'
        elif name.endswith('.docx') and docx:
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                data += para.text + '\n'
        else:
            st.warning("Dateityp nicht unterstützt oder Parser fehlt.")
    except Exception as e:
        st.error(f"Fehler beim Einlesen der Datei: {e}")
    return data.strip()

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
        progress = st.progress(0)
        st.info("Debatte läuft...")
        progress.progress(10)
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
        progress.progress(30)
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        model = "gpt-3.5-turbo"
        content = debate_call(api_key, api_url, model, prompt)
        if not content:
            st.error("Keine Antwort erhalten.")
            return
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = extract_json_fallback(content)
            show_debug_output(content)
        st.markdown(f"**Dauer:** {len(content)} Zeichen")
        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))

# === Neu-Version ===
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")

    # Input-Bereich mit Datei-Upload
    input_text = st.text_area("Deine Idee/Businessplan/Thema:", height=150)
    uploaded = st.file_uploader(label="➕ Datei hochladen", type=["pdf","txt","docx"], help="Datei hier hochladen")
    if uploaded:
        parsed = parse_uploaded_file(uploaded)
        if parsed:
            input_text = parsed
            st.success("📎 Datei erfolgreich eingelesen.")

    # Modelle auswählen mit diskussionsstart-Auswahl
    col1, col2 = st.columns(2)
    model_a = col1.selectbox("Modell für Agent A", ["gpt-3.5-turbo","gpt-4"], key="neu_a")
    model_b = col2.selectbox("Modell für Agent B", ["gpt-3.5-turbo","gpt-4"], key="neu_b")

    # Kurze, kommentarlos platzierte Auswahl: wer startet
    starter = st.radio("", ["Agent A", "Agent B"], horizontal=True)

    # Prompt-Modus für Agent B für Agent B
    mode = st.radio(
        "Prompt-Modus",
        ["Getrennter Prompt für B", "Gleicher Prompt für beide"],
        key="modus"
    )
    prompt_b = st.text_area(
        "Prompt für Agent B:" if mode == "Getrennter Prompt für B" else "Gemeinsamer Prompt:",
        height=100,
        key="prompt_b"
    )

    # Diskussion starten
    if st.button("Diskussion starten", key="start_neu"):
        if not input_text:
            st.error("Bitte Input eingeben oder Datei hochladen.")
            return
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        prompt_a = input_text
        prompt_b_final = prompt_b if prompt_b else input_text

        if starter == "Agent A":
            resp_a = debate_call(api_key, api_url, model_a, prompt_a)
            resp_b = debate_call(api_key, api_url, model_b, prompt_b_final)
        else:
            resp_b = debate_call(api_key, api_url, model_b, prompt_b_final)
            resp_a = debate_call(api_key, api_url, model_a, prompt_a)

        st.markdown("### 🗣️ Antwort Agent A")
        st.write(resp_a or "Keine Antwort.")
        st.markdown("### 🗣️ Antwort Agent B")
        st.write(resp_b or "Keine Antwort.")

# Version-Auswahl
version = st.selectbox("Version:", ["Grundversion","Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
