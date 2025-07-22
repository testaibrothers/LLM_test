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

# === Grundversion UI ===
def run_grundversion():
    st.title("🤖 KI-Debattenplattform – Grundversion")
    st.subheader("Single-Call Debatte mit OpenAI")

    # Input über einfaches Textfeld
    input_text = st.text_input("📝 Thema für die Diskussion eingeben:")
    start = st.button("💬 Diskussion starten")

    if start and input_text:
        st.info("Debatte läuft...")
        prompt = (
            f"Thema: '{input_text}'\n"
            "Agent A (optimistisch)\nAgent B (pessimistisch)\n"
            "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
        )
        content = debate_call(st.secrets.get("openai_api_key", ""),
                               "https://api.openai.com/v1/chat/completions",
                               "gpt-3.5-turbo", prompt)
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

# === NeuVersion UI ===
def run_neuversion():
    st.title("🤖 KI-Debattenplattform – NeuVersion")
    st.subheader("Single-Call Debatte mit OpenAI – erweiterter Input")

    # Input für Agent A: Textfeld oder Datei-Upload
    st.markdown("### 💡 Deine Idee oder Frage für Agent A")
    st.markdown("⚠️ Hinweis: Agent A beginnt immer die Diskussion.")
    input_text = st.text_area("📝 Thema, Idee oder Businessplan eingeben:", height=200)
    uploaded_file = st.file_uploader("📎 Datei hochladen (pdf, txt, docx)", type=["pdf", "txt", "docx"])

    # Dateiinhalt extrahieren
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            import fitz
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            input_text = "\n".join(page.get_text() for page in doc)
        elif uploaded_file.type == "text/plain":
            input_text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.type.startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
            import docx
            doc = docx.Document(uploaded_file)
            input_text = "\n".join([p.text for p in doc.paragraphs])

    # Hinweis über Auswahl
    st.markdown("⚠️ Agent A startet stets die Diskussion, unabhängig von der Use-Case-Auswahl.")

    # Use Case Auswahl
    use_case = st.selectbox(
        "Use Case auswählen:",
        ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"],
        index=0
    )
    start = st.button("💬 Diskussion starten")

    if start and input_text:
        progress = st.progress(0)
        st.info("Debatte läuft...")
        progress.progress(10)

        if use_case == "Allgemeine Diskussion":
            prompt = (
                f"Thema: '{input_text}'\n"
                "Agent A (optimistisch)\nAgent B (pessimistisch)\n"
                "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
            )
        else:
            prompt = (
                f"Thema: '{input_text}'\n"
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

# === Version-Switch ===
version = st.selectbox("Version:", ["Grundversion", "NeuVersion"], index=0)
if version == "Grundversion":
    run_grundversion()
elif version == "NeuVersion":
    run_neuversion()
