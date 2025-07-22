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
    st.sidebar.info("Hinweis: Agent A startet immer die Diskussion mit deiner Eingabe.")

    # Eingabe-Feld oder Datei-Upload für Idee/Businessplan/Thema im Hauptbereich
    st.subheader("Deine Idee/Businessplan/Thema eingeben oder hochladen")
    input_text = st.text_area("", value=st.session_state.get("input_text", ""), height=150, key="input_text")
    uploaded_file = st.file_uploader(
        "Oder lade eine Datei hoch (pdf, txt, docx):", type=["pdf", "txt", "docx"], key="upload"
    )
    if uploaded_file:
        try:
            raw = uploaded_file.read()
            if uploaded_file.type == "application/pdf":
                import io, PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(raw))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            else:
                text = raw.decode("utf-8", errors="ignore")
            input_text = text
            st.session_state["input_text"] = input_text
        except Exception as e:
            st.error(f"Fehler beim Lesen der Datei: {e}")

    # Modelle und Prompt-Modus in der Sidebar
    model_list = ["gpt-3.5-turbo", "gpt-4"]
    model_a = st.sidebar.selectbox("Modell für Agent A", model_list, index=0)
    model_b = st.sidebar.selectbox("Modell für Agent B", model_list, index=1)
    st.sidebar.markdown("---")
    mode = st.sidebar.radio("Prompt-Modus", ["Getrennter Prompt für A und B", "Gleicher Prompt für beide"], index=0)

    # Prompt-Felder vorbefüllen
    if mode == "Getrennter Prompt für A und B":
        prompt_a = st.text_area("Prompt für Agent A", value=input_text, height=100, key="prompt_a_area")
        prompt_b = st.text_area("Prompt für Agent B", value=st.session_state.get("prompt_b_area", ""), height=100, key="prompt_b_area")
    else:
        prompt_shared = st.text_area("Gleicher Prompt für beide", value=input_text, height=100, key="shared_area")
        prompt_a = prompt_b = prompt_shared

    if st.button("Diskussion starten"):
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = st.secrets.get("openai_api_key", "")
        response_a = debate_call(api_key, api_url, model_a, prompt_a)
        response_b = debate_call(api_key, api_url, model_b, prompt_b)

        st.markdown("### 🗣️ Antwort Agent A")
        st.write(response_a or "Keine Antwort")
        st.markdown("### 🗣️ Antwort Agent B")
        st.write(response_b or "Keine Antwort")

# Version-Auswahl permanent in der Sidebar
st.sidebar.markdown("---")
version = st.sidebar.selectbox("Version:", ["Grundversion", "Neu-Version"], index=1)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
