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
        duration = time.time() - progress._ctx.start_time if hasattr(progress._ctx, 'start_time') else 0  # fallback
        if not content:
            st.error("Keine Antwort erhalten.")
            return

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = extract_json_fallback(content)
            show_debug_output(content)

        st.markdown(f"**Dauer:** {duration:.2f}s")
        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))

# === Neu-Version ===
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neu-Version")
    st.info("Hinweis: Agent A startet immer die Diskussion basierend auf deinem Input.")

    # Sidebar: Prompt-Generator
    with st.sidebar.expander("🧠 Prompt-Generator", expanded=False):
        keyword = st.text_input("Schlagwort eingeben:", key="kw_gen")
        if st.button("Prompt generieren", key="gen_btn") and keyword:
            try:
                template = open("promptgen_header.txt", encoding="utf-8").read().strip()
                filled_prompt = template.replace("[SCHLAGWORT]", keyword)
                api_url = "https://api.openai.com/v1/chat/completions"
                api_key = st.secrets.get("openai_api_key", "")
                response = debate_call(api_key, api_url, "gpt-3.5-turbo", filled_prompt)
                filled_prompt = response or "[Fehler bei der Generierung]"
            except Exception:
                filled_prompt = "[Promptdatei fehlt]"
            st.session_state["last_generated"] = filled_prompt
        st.text_area("Vorschlag:", value=st.session_state.get("last_generated", ""), height=100)
        colA, colB = st.columns(2)
        if colA.button("In A übernehmen", key="toA"):
            st.session_state["prompt_a"] = st.session_state.get("last_generated", "")
        if colB.button("In B übernehmen", key="toB"):
            st.session_state["prompt_b"] = st.session_state.get("last_generated", "")

    # Input: Text oder Datei
    input_text = st.text_area("Deine Idee/Businessplan/Thema:", height=150)
    uploaded = st.file_uploader("Oder lade eine Datei hoch (PDF, TXT, DOCX):", type=["pdf","txt","docx"])
    if uploaded:
        parsed = parse_uploaded_file(uploaded)
        if parsed:
            input_text = parsed
            st.success("Datei eingelesen.")

    # Modelle
    col1, col2 = st.columns(2)
    model_a = col1.selectbox("Modell für Agent A", ["gpt-3.5-turbo","gpt-4"], key="neu_a")
    model_b = col2.selectbox("Modell für Agent B", ["gpt-3.5-turbo","gpt-4"], key="neu_b")

    # Prompt-Modus
    mode = st.radio("Prompt-Modus", ["Getrennter Prompt für B","Gleicher Prompt für beide"], key="modus")
    prompt_b = st.text_area("Prompt für Agent B:" if mode=="Getrennter Prompt für B" else "Gemeinsamer Prompt:", height=100, key="prompt_b")

    if st.button("Diskussion starten", key="start_neu"):
        if not input_text:
            st.error("Bitte Input eingeben oder Datei hochladen.")
            return
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        prompt_a = st.session_state.get("prompt_a", input_text)
        resp_a = debate_call(api_key, api_url, model_a, prompt_a)
        resp_b = debate_call(api_key, api_url, model_b, prompt_b)
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
