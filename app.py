# Projekt: LLM-Debate Plattform (MVP)
# Ziel: Auswahl von zwei LLMs für Diskussion mit vollwertiger Debatten-Logik in Grundversion und Prototyp-Neu-Version

import streamlit as st
import requests
import time
import json

# --- Funktion: Grundversion mit vollständiger Debatten-Engine ---
def run_grundversion():
    st.title("🤖 KI-Debattenplattform – Grundversion")
    # Agenten-Modelle (funktional für OpenAI und Groq fest kodiert)
    llm_list = ["gpt-3.5-turbo", "claude-3"]  # Nur unterstützte Modelle in Grundversion
    col1, col2 = st.columns(2)
    with col1:
        agent_a_model = st.selectbox("Agent A LLM:", llm_list, index=0, key="grund_a")
    with col2:
        agent_b_model = st.selectbox("Agent B LLM:", llm_list, index=1, key="grund_b")
    # Frage
    action = st.button("Diskussion starten", key="grund_action")
    user_question = st.text_area("Deine Fragestellung:", key="grund_q")

    if action and user_question:
        # Debatten-Logik
        SYSTEM_A = {"gpt-3.5-turbo": "Du bist Agent A – optimistischer Debattierer.",
                    "claude-3": "Du bist Agent A – optimistischer Debattierer."}[agent_a_model]
        SYSTEM_B = {"gpt-3.5-turbo": "Du bist Agent B – kritischer Skeptiker.",
                    "claude-3": "Du bist Agent B – kritischer Skeptiker."}[agent_b_model]
        history = []
        MAX_ROUNDS = 6
        threshold = 0.8
        # Embedding-Funktion placeholder
        def similarity(a, b):
            # Simple token overlap heuristic
            sa, sb = set(a.split()), set(b.split())
            return len(sa & sb) / max(len(sa), len(sb)) if sa and sb else 0

        for i in range(MAX_ROUNDS):
            # Agent A Anfrage
            msg_a = requests.post(
                f"https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {st.secrets['openai_api_key']}", "Content-Type": "application/json"},
                json={"model": agent_a_model,
                      "messages": [{"role":"system","content":SYSTEM_A}] + history + [{"role":"user","content":user_question}],
                      "temperature":0.7}
            ).json()["choices"][0]["message"]["content"]
            history.append({"role":"assistant","content": msg_a})

            # Agent B Anfrage
            msg_b = requests.post(
                f"https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {st.secrets['openai_api_key']}", "Content-Type": "application/json"},
                json={"model": agent_b_model,
                      "messages": [{"role":"system","content":SYSTEM_B}] + history + [{"role":"user","content":user_question}],
                      "temperature":0.7}
            ).json()["choices"][0]["message"]["content"]
            history.append({"role":"assistant","content": msg_b})

            # Abbruch bei Einigung
            if similarity(msg_a, msg_b) >= threshold:
                final = msg_a
                break
        else:
            # Referee
            REF = "Du bist Referee – fasse zusammen und gib Empfehlung."
            final = requests.post(
                f"https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {st.secrets['openai_api_key']}", "Content-Type": "application/json"},
                json={"model": agent_a_model,
                      "messages": [{"role":"system","content":REF}] + history,
                      "temperature":0.7}
            ).json()["choices"][0]["message"]["content"]

        # Ausgabe
        st.success("✅ Einigung gefunden")
        st.markdown(final)

# --- Funktion: Prototyp Neu-Version (kosmetisch) ---
def run_neu():
    st.title("🤖 KI-Debattenplattform – Neueste Version")
    llm_list = ["gpt-3.5-turbo", "gpt-4", "claude-3", "mistral-7b", "llama-2-13b"]
    col1, col2 = st.columns(2)
    with col1:
        a = st.selectbox("Agent A LLM:", llm_list, index=0, key="neu_a")
    with col2:
        b = st.selectbox("Agent B LLM:", llm_list, index=1, key="neu_b")
    act = st.button("Diskussion starten", key="neu_act")
    q = st.text_area("Deine Fragestellung:", key="neu_q")
    if act and q:
        st.markdown(f"Modelle: A={a}, B={b}")
        st.info("Neu-Version: Implementierung folgt")

# === UI-Steuerung ===
version = st.selectbox("Version:", ["Grundversion", "Neu"], index=0)
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()
