# LLM-Debatte – Einfache Komplettversion in einer Datei (nur OpenAI)
import streamlit as st
import requests
import json
import re
import time

# === Page Configuration ===
st.set_page_config(page_title="KI-Debattenplattform", layout="centered")

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
def debate_call(api_key, api_url, model, prompt, temperature=0.2, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "system", "content": prompt}], "temperature": temperature, "max_tokens": 200}
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

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "saved_topics" not in st.session_state:
    st.session_state.saved_topics = {}

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
        prompt = (f"Thema: '{question}'\n" +
                  ("Agent A (optimistisch)\nAgent B (pessimistisch)\n" if use_case == "Allgemeine Diskussion" else "Agent A analysiert Chancen.\nAgent B analysiert Risiken.\n") +
                  "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation.")
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
    import numpy as np
    st.title("🤖 KI-Debattenplattform – Neu-Version")
    # Sidebar: Prompt-Generator & Einstellungen
    with st.sidebar:
        with st.expander("🧠 Prompt-Generator", expanded=False):
            keyword = st.text_input("Schlagwort eingeben:")
            if st.button("Prompt generieren") and keyword:
                try:
                    with open("promptgen_header.txt", "r", encoding="utf-8") as f:
                        template = f.read().strip()
                    gen_prompt = template.replace("[SCHLAGWORT]", keyword)
                    gen_resp = debate_call(
                        st.secrets.get("openai_api_key", ""),
                        "https://api.openai.com/v1/chat/completions",
                        "gpt-3.5-turbo", gen_prompt
                    )
                    st.session_state.prompt_a = gen_resp or ""
                    st.session_state.prompt_b = gen_resp or ""
                except FileNotFoundError:
                    st.session_state.prompt_a = ""
                    st.session_state.prompt_b = ""
            st.text_area("Vorschlag", st.session_state.get("prompt_a", ""), height=100)
        with st.expander("⚙️ Einstellungen", expanded=True):
            start_agent = st.selectbox(
                "Welcher Agent startet?", ["Agent A", "Agent B"], key="start_agent",
                help="Wählt aus, welcher Agent zuerst mit der Diskussion beginnt."
            )
            max_rounds_opt = ["Endlos"] + list(range(1, 101))
            max_rounds = st.selectbox(
                "Maximale Runden", max_rounds_opt, key="max_rounds",
                help="Legt die maximale Anzahl hin- und her Nachrichten fest. 'Endlos' bedeutet keine Begrenzung."
            )
            temp_a = st.slider(
                "Temperatur Agent A", 0.0, 1.0, 0.7, 0.05, key="temperature_a",
                help="Steuert die Kreativität: 0.0 sehr deterministisch, 1.0 sehr variabel."
            )
            temp_b = st.slider(
                "Temperatur Agent B", 0.0, 1.0, 0.7, 0.05, key="temperature_b",
                help="Steuert die Kreativität: 0.0 sehr deterministisch, 1.0 sehr variabel."
            )
            st.checkbox(
                "Manuelle Bestätigung zwischen Runden?", key="manual_pause",
                help="Erfordert nach jeder Runde eine Bestätigung bevor es weitergeht."
            )
            st.text_input(
                "Thema speichern unter", key="save_topic",
                help="Gib einen Namen ein, unter dem die aktuelle Idee gespeichert wird."
            )
            if st.button("Thema speichern"):
                name = st.session_state.get("save_topic")
                st.session_state.saved_topics[name] = st.session_state.idea_text or ""
                st.success(f"Thema '{name}' gespeichert.")
            topic_list = list(st.session_state.saved_topics.keys())
            if topic_list:
                choice = st.selectbox(
                    "Gespeicherte Themen laden", topic_list, key="load_topic",
                    help="Lädt ein zuvor gespeichertes Thema."
                )
                if st.button("Laden"):
                    st.session_state.idea_text = st.session_state.saved_topics.get(choice, "")
            st.download_button(
                "Sitzungsprotokoll herunterladen", data=json.dumps(st.session_state.chat_history), file_name="session.json",
                help="Lädt das Protokoll der aktuellen Sitzung als JSON-Datei herunter."
            )

    # Main content
    st.text(" ")  # Abstand zum Sidebar
    idea = st.text_area("Deine Idee / Businessplan / Thema:", key="idea_text")
    col1, col2 = st.columns(2)
    with col1:
        model_a = st.selectbox("Modell Agent A", ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"], key="neu_a")
        prompt_a = st.text_area("Prompt Agent A", st.session_state.get("prompt_a", ""), height=120)
    with col2:
        model_b = st.selectbox("Modell Agent B", ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"], key="neu_b")
        prompt_b = st.text_area("Prompt Agent B", st.session_state.get("prompt_b", ""), height=120)

    if st.button("Diskussion starten") and st.session_state.get("idea_text"):
        api_key = st.secrets.get("openai_api_key", "")
        api_url = "https://api.openai.com/v1"
                # Consensus loop
        history = []
        for i in range(1, 101 if st.session_state.max_rounds != "Endlos" else 10000):
            # Agent response
            agent = st.session_state.start_agent
            model = model_a if agent == "Agent A" else model_b
            temp = st.session_state.temperature_a if agent == "Agent A" else st.session_state.temperature_b
            # Zusammenführung der Idee und des jeweiligen Prompts
                        # Zusammenführung der Idee und des jeweiligen Prompts
                        # Zusammenführung der Idee und des jeweiligen Prompts
            prompt = st.session_state.idea_text + "
" + (prompt_a if agent == "Agent A" else prompt_b)
            resp = debate_call(api_key, api_url + "/chat/completions", model, prompt, temperature=temp)(api_key, api_url + "/chat/completions", model, prompt, temperature=temp)
            resp = debate_call(api_key, api_url + "/chat/completions", model, prompt, temperature=temp)
            history.append((agent, resp))
            # Switch agent
            st.session_state.start_agent = "Agent B" if agent == "Agent A" else "Agent A"
            # Compute embeddings
            emb_a = requests.post(
                api_url + "/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "text-embedding-ada-002", "input": history[-2][1] if agent == "Agent B" else history[-1][1]}
            ).json()["data"][0]["embedding"]
            emb_b = requests.post(
                api_url + "/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "text-embedding-ada-002", "input": history[-1][1] if agent == "Agent B" else history[-2][1]}
            ).json()["data"][0]["embedding"]
            sim = np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b))
            if sim >= 0.8:
                st.success(f"Konsens nach {i} Runden erreicht (Similarity={sim:.2f})")
                break
            if st.session_state.manual_pause:
                st.button("Weiter zur nächsten Runde")
        # Show last response
        last_agent, last_resp = history[-1]
        st.markdown(f"### 🗣️ Antwort von {last_agent}")
        st.write(last_resp)
        st.session_state.chat_history.extend([{"agent": a, "response": r} for a, r in history])
        # Anzeige der Uneinigkeit (untersten 20% semantische Ähnlichkeit)
        if len(history) >= 2:
            last_A = history[-2][1]
            last_B = history[-1][1]
            # Aufteilung in Sätze 
            sents_A = re.split(r'(?<=[\.!?]) +', last_A)
            sents_B = re.split(r'(?<=[\.!?]) +', last_B)
            # Berechnung von Satz-Embeddings
            emb_A = [requests.post(api_url + "/embeddings", headers={"Authorization": f"Bearer {api_key}"}, json={"model": "text-embedding-ada-002", "input": s}).json()["data"][0]["embedding"] for s in sents_A]
            emb_B = [requests.post(api_url + "/embeddings", headers={"Authorization": f"Bearer {api_key}"}, json={"model": "text-embedding-ada-002", "input": s}).json()["data"][0]["embedding"] for s in sents_B]
            # Ähnlichkeitsmatrix
            sims = [(i, j, np.dot(ea, eb)/(np.linalg.norm(ea)*np.linalg.norm(eb))) for i, ea in enumerate(emb_A) for j, eb in enumerate(emb_B)]
            # sortiere aufsteigend und nimm unterste 20%
            sims_sorted = sorted(sims, key=lambda x: x[2])
            cutoff = max(1, int(len(sims_sorted)*0.2))
            low = sims_sorted[:cutoff]
            with st.expander("Uneinigkeit anzeigen (unterste 20%)"):
                for i, j, sim in low:
                    st.markdown(f"- A (Satz {i+1}): {sents_A[i]}
  B (Satz {j+1}): {sents_B[j]}  _(sim={sim:.2f})_")

version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
