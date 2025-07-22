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
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"API-Fehler {resp.status_code}: {resp.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Verbindungsfehler: {e}")
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
                text = page.extract_text() or ''
                data += text + '\n'
        elif name.endswith('.docx') and docx:
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                data += para.text + '\n'
        else:
            st.warning("Keine geeignete Parser-Bibliothek gefunden oder Dateityp nicht unterstützt.")
    except Exception as e:
        st.error(f"Fehler beim Einlesen der Datei: {e}")
    return data.strip()

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
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))
        progress.progress(100)

# === Neu-Version ===
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")

    # Hinweis für Agent A
    st.info("Hinweis: Agent A startet immer die Diskussion basierend auf deinem Input.")

    # Eingabe: Text oder Datei
    input_text = st.text_area(
        "Gib hier deine Idee, deinen Businessplan oder dein Thema ein:",
        height=150
    )
    uploaded_file = st.file_uploader(
        "Oder lade deine Datei hoch (PDF, TXT, DOCX):",
        type=['pdf', 'txt', 'docx']
    )
    if uploaded_file:
        file_content = parse_uploaded_file(uploaded_file)
        if file_content:
            input_text = file_content
            st.success("Datei erfolgreich eingelesen.")

    # Model-Auswahl
    col1, col2 = st.columns(2)
    with col1:
        model_a = st.selectbox("Modell für Agent A", ["gpt-3.5-turbo", "gpt-4"], key="neu_a")
    with col2:
        model_b = st.selectbox("Modell für Agent B", ["gpt-3.5-turbo", "gpt-4"], key="neu_b")

    st.markdown("### Prompt-Modus")
    mode = st.radio(
        "Eingabemodus",
        ["Getrennter Prompt für Agent B", "Gleicher Prompt für beide"],
        key="modus"
    )

    # Prompt für Agent B oder Shared
    if mode == "Getrennter Prompt für Agent B":
        prompt_b = st.text_area(
            "Prompt für Agent B:",
            height=100,
            key="prompt_b"
        )
    else:
        shared = st.text_area(
            "Gemeinsamer Prompt (wird auch für Agent B verwendet):",
            height=100,
            key="shared"
        )
        prompt_b = shared

    # Diskussion starten
    start = st.button("Diskussion starten", key="start_neu")
    if start:
        if not input_text:
            st.error("Bitte gib einen Text ein oder lade eine Datei hoch, um die Diskussion zu starten.")
            return

        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")

        # Agent A
        response_a = debate_call(api_key, api_url, model_a, input_text)
        # Agent B
        response_b = debate_call(api_key, api_url, model_b, prompt_b)

        st.markdown("### 🗣️ Antwort Agent A")
        st.write(response_a or "Keine Antwort von Agent A.")
        st.markdown("### 🗣️ Antwort Agent B")
        st.write(response_b or "Keine Antwort von Agent B.")

# Version-Auswahl
e
version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
