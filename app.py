# LLM-Debatte – Einfache Komplettversion in einer Datei (nur OpenAI)
import streamlit as st
import requests
import json
import re
import time
import numpy as np

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
    resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    st.error(f"API-Fehler {resp.status_code}: {resp.text}")
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
    st.title("🤖 KI-Debattenplattform – Neu-Version")
    # Sidebar: Prompt-Generator, Einstellungen & Kostenschätzer
    with st.sidebar:
        with st.expander("🧠 Prompt-Generator", expanded=False):
            keyword = st.text_input("Schlagwort eingeben:")
            if st.button("Prompt generieren") and keyword:
                try:
                    template = open("promptgen_header.txt", encoding="utf-8").read().strip()
                    gen_prompt = template.replace("[SCHLAGWORT]", keyword)
                    gen_resp = debate_call(st.secrets.get("openai_api_key", ""),
                                           "https://api.openai.com/v1/chat/completions",
                                           "gpt-3.5-turbo", gen_prompt)
                    st.session_state.prompt_a = gen_resp or ""
                    st.session_state.prompt_b = gen_resp or ""
                except FileNotFoundError:
                    st.session_state.prompt_a = ""
                    st.session_state.prompt_b = ""
            st.text_area("Vorschlag", st.session_state.get("prompt_a", ""), height=100)
        with st.expander("⚙️ Einstellungen", expanded=True):
            st.selectbox("Welcher Agent startet?", ["Agent A", "Agent B"], key="start_agent",
                         help="Legt fest, welcher Agent zuerst spricht.")
            st.selectbox("Maximale Runden", ["Endlos"]+list(range(1,101)), key="max_rounds",
                         help="Begrenzt den Dialog auf die angegebene Anzahl.")
            st.slider("Temperatur Agent A", 0.0,1.0,0.7,0.05, key="temperature_a",
                      help="Kreativität A: 0.0 deterministisch, 1.0 variabel.")
            st.slider("Temperatur Agent B", 0.0,1.0,0.7,0.05, key="temperature_b",
                      help="Kreativität B: 0.0 deterministisch, 1.0 variabel.")
            st.number_input("Konsens-Schwelle (%)", min_value=0, max_value=100, value=80, key="consensus_thresh",
                            help="Prozentuale Ähnlichkeit, ab der Konsens gilt.")
            st.checkbox("Manuelle Bestätigung zwischen Runden?", key="manual_pause",
                        help="Erfordert Klick für nächste Runde.")
            st.text_input("Thema speichern unter", key="save_topic", help="Speichert aktuelle Idee.")
            if st.button("Thema speichern"):
                name=st.session_state.save_topic
                st.session_state.saved_topics[name]=st.session_state.idea_text or ""
                st.success(f"Thema '{name}' gespeichert.")
            if st.session_state.saved_topics:
                ch=st.selectbox("Gespeicherte Themen laden", list(st.session_state.saved_topics.keys()), key="load_topic",
                                help="Lädt ein gespeichertes Thema.")
                if st.button("Laden"):
                    st.session_state.idea_text=st.session_state.saved_topics[ch]
            st.download_button("Sitzungsprotokoll herunterladen", data=json.dumps(st.session_state.chat_history), file_name="session.json",
                               help="Exportiert Chat-Historie als JSON.")

    # Main content
    st.text(" ")
    idea = st.text_area("Deine Idee / Businessplan / Thema:", key="idea_text")
    col1,col2=st.columns(2)
    with col1:
        model_a=st.selectbox("Modell Agent A",["gpt-3.5-turbo","gpt-3.5-turbo-16k","gpt-4","gpt-4-32k"],key="neu_a")
        prompt_a=st.text_area("Prompt Agent A",st.session_state.get("prompt_a",""),height=120)
    with col2:
        model_b=st.selectbox("Modell Agent B",["gpt-3.5-turbo","gpt-3.5-turbo-16k","gpt-4","gpt-4-32k"],key="neu_b")
        prompt_b=st.text_area("Prompt Agent B",st.session_state.get("prompt_b",""),height=120)

    if st.button("Diskussion starten") and st.session_state.get("idea_text"):
        api_key=st.secrets.get("openai_api_key","")
        api_url="https://api.openai.com/v1"
        history=[]
        # iterative loop until consensus or max
        for i in range(1, 10001 if st.session_state.max_rounds=="Endlos" else st.session_state.max_rounds+1):
            agent=st.session_state.start_agent
            model=model_a if agent=="Agent A" else model_b
            temp=st.session_state.temperature_a if agent=="Agent A" else st.session_state.temperature_b
            prompt_text=idea+"\n"+(prompt_a if agent=="Agent A" else prompt_b)
            resp=debate_call(api_key, api_url+"/chat/completions",model,prompt_text,temperature=temp)
            history.append((agent,resp))
            # switch
            st.session_state.start_agent="Agent B" if agent=="Agent A" else "Agent A"
            # compute similarity
            if len(history)>1:
                last_A=history[-2][1]; last_B=history[-1][1]
                emb_A=requests.post(api_url+"/embeddings",headers={"Authorization":f"Bearer {api_key}"},json={"model":"text-embedding-ada-002","input":last_A}).json()["data"][0]["embedding"]
                emb_B=requests.post(api_url+"/embeddings",headers={"Authorization":f"Bearer {api_key}"},json={"model":"text-embedding-ada-002","input":last_B}).json()["data"][0]["embedding"]
                sim=np.dot(emb_A,emb_B)/(np.linalg.norm(emb_A)*np.linalg.norm(emb_B))
                if sim>=st.session_state.consensus_thresh/100:
                    st.success(f"Konsens ({sim:.2f}) nach {i} Runden erreicht")
                    break
                if st.session_state.manual_pause:
                    st.button("Weiter")
                # Finale Konsens-Zeile (Textfeld)
        st.markdown("### 🏁 Finaler Konsens")
        consensus_text = history[-1][1] if history else ""
        st.text_area("Konsens:", value=consensus_text, height=150)

        # show responses
        for a,r in history:
            st.markdown(f"### 🗣️ Antwort von {a}")
            st.write(r)
        # show uneinigkeit
        if len(history)>1:
            last_A=history[-2][1]; last_B=history[-1][1]
            sents_A=re.split(r'(?<=[\.!?]) +',last_A); sents_B=re.split(r'(?<=[\.!?]) +',last_B)
            emb_A=[requests.post(api_url+"/embeddings",headers={"Authorization":f"Bearer {api_key}"},json={"model":"text-embedding-ada-002","input":s}).json()["data"][0]["embedding"] for s in sents_A]
            emb_B=[requests.post(api_url+"/embeddings",headers={"Authorization":f"Bearer {api_key}"},json={"model":"text-embedding-ada-002","input":s}).json()["data"][0]["embedding"] for s in sents_B]
            sims=[(i,j,np.dot(ea,eb)/(np.linalg.norm(ea)*np.linalg.norm(eb))) for i,ea in enumerate(emb_A) for j,eb in enumerate(emb_B)]
            low=sorted(sims,key=lambda x:x[2])[:max(1,int(len(sims)*0.2))]
            st.markdown("### ⚡ Uneinigkeit (unterste 20%)")
            for i,j,sm in low:
                st.write(f"A Satz {i+1}: {sents_A[i]}")
                st.write(f"B Satz {j+1}: {sents_B[j]}")
                st.write(f"Similarity: {sm:.2f}")

version=st.selectbox("Version:",["Grundversion","Neu-Version"],index=0)
if version=="Grundversion": run_grundversion()
else: run_neu()
