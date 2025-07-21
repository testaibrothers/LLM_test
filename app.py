# Projekt: LLM-Debate Plattform (MVP)
# Ziel: Auswahl von zwei LLMs für Diskussion (UI-Prototyp)

import streamlit as st
import requests
import time
import json

# === UI + Konfiguration ===
# Dropdown: Version auswählen
version = st.selectbox("Version:", ["Grundversion", "Neu"], index=0)


# Dynamischer Einstieg basierend auf Version
if version == "Grundversion":
    run_grundversion()
else:
    run_neu()

# Definition der beiden Versionen als Funktionen

def run_grundversion():
    st.title("🤖 KI-Debattenplattform – Grundversion")
    # Agenten-Modelle auswählen (kosmetisch)
    llm_list = ["gpt-3.5-turbo","gpt-4","claude-3","mistral-7b","llama-2-13b"]
    col1, col2 = st.columns(2)
    with col1:
        agent_a_model = st.selectbox("Agent A LLM:", llm_list, index=0, key="grund_a")
    with col2:
        agent_b_model = st.selectbox("Agent B LLM:", llm_list, index=1, key="grund_b")
    # Nutzerfrage
    action = st.button("Diskussion starten", key="grund_action")
    user_question = st.text_area("Deine Fragestellung:", key="grund_q")
    if action and user_question:
        st.markdown(f"**Ausgewählte Modelle:** Agent A = {agent_a_model}, Agent B = {agent_b_model}")
        st.markdown(f"**Frage:** {user_question}")
        st.info("Grundversion: Platzhalter-Debatte läuft...")


def run_neu():
    st.title("🤖 KI-Debattenplattform – Neueste Version")
    # Agenten-Modelle auswählen (kosmetisch)
    llm_list = ["gpt-3.5-turbo","gpt-4","claude-3","mistral-7b","llama-2-13b"]
    col1, col2 = st.columns(2)
    with col1:
        agent_a_model = st.selectbox("Agent A LLM:", llm_list, index=0, key="neu_a")
    with col2:
        agent_b_model = st.selectbox("Agent B LLM:", llm_list, index=1, key="neu_b")
    # Nutzerfrage
    action = st.button("Diskussion starten", key="neu_action")
    user_question = st.text_area("Deine Fragestellung:", key="neu_q")
    if action and user_question:
        st.markdown(f"**Ausgewählte Modelle:** Agent A = {agent_a_model}, Agent B = {agent_b_model}")
        st.markdown(f"**Frage:** {user_question}")
        st.info("Neueste Version: Platzhalter-Debatte läuft...")

# Agenten-Modelle auswählen (kosmetisch)
llm_list = [
    "gpt-3.5-turbo",
    "gpt-4",
    "claude-3",
    "mistral-7b",
    "llama-2-13b"
]
col1, col2 = st.columns(2)
with col1:
    agent_a_model = st.selectbox("Agent A LLM:", llm_list, index=0)
with col2:
    agent_b_model = st.selectbox("Agent B LLM:", llm_list, index=1)

# Nutzerfrage
action = st.button("Diskussion starten")
user_question = st.text_area("Deine Fragestellung:")

# Platzhalter: Hier würde die Debatte orchestriert werden
if action and user_question:
    st.markdown(f"**Ausgewählte Modelle:** Agent A = {agent_a_model}, Agent B = {agent_b_model}")
    st.markdown(f"**Frage:** {user_question}")
    st.info("Debatte wird durchgeführt... (Implementierung folgt)")
