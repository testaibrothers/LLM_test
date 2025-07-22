# LLM-Debate Plattform (MVP) – Modular, aber als OneFile-Version (Fehlerfrei)
# Alles in einer Datei: Einfacher Import, keine Modul-Probleme
import streamlit as st
import requests
import time
import json

# === Konfig & Konstanten ===
PROVIDERS = ["OpenAI (gpt-3.5-turbo)", "Groq (Mistral-saba-24b)"]
USE_CASES = ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"]
LLM_LIST = ["gpt-3.5-turbo", "gpt-4", "claude-3", "mistral-saba-24b", "llama-2-13b"]

def get_api_conf(provider):
    if provider.startswith("OpenAI"):
        return "https://api.openai.com/v1/chat/completions", st.secrets.get("openai_api_key", ""), "gpt-3.5-turbo", 0.002
    else:
        return "https://api.groq.com/openai/v1/chat/completions", st.secrets.get("groq_api_key", ""), "mistral-saba-24b", 0.0

# === Prompt-Handling ===
def load_prompt_template(path="prompt_template.txt"):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_prompt_template(content, path="prompt_template.txt"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def build_final_prompt(user_keyword, path="prompt_template.txt"):
    template = load_prompt_template(path)
    return template.replace("[SCHLAGWORT]", user_keyword)

def parse_json_response(content):
    raw = content.strip()
    if raw.startswith("```") and raw.endswith("```"):
        raw = "\n".join(raw.splitlines()[1:-1])
    try:
        data = json.loads(raw)
    except:
        data = {}
    return data, raw

# === API-Calls ===
def debate_call(selected_provider, api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "system", "content": prompt}], "temperature": 0.7}
    while True:
        resp = requests.post(api_url, headers=headers, json=payload)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"], selected_provider
        if resp.status_code == 429:
            error = resp.json().get("error", {})
            if selected_provider.startswith("OpenAI") and error.get("code") == "insufficient_quota":
                st.warning("OpenAI-Quota erschöpft, wechsle automatisch zu Groq...")
                return debate_call(
                    "Groq (Mistral-saba-24b)",
                    st.secrets.get("groq_api_key", ""),
                    "https://api.groq.com/openai/v1/chat/completions",
                    "mistral-saba-24b",
                    prompt,
                    timeout
                )
            st.warning(f"Rate Limit bei {selected_provider}. Warte {timeout}s...")
            time.sleep(timeout)
            continue
        st.error(f"API-Fehler {resp.status_code}: {resp.text}")
        return None, selected_provider

def generate_prompt_grok(final_prompt):
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    groq_key = st.secrets.get("groq_api_key", "")
    payload = {
        "model": "mistral-saba-24b",
        "messages": [
            {"role": "system", "content": final_prompt},
        ],
        "temperature": 0.7
    }
    resp = requests.post(groq_url, headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}, json=payload)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"Generator-API-Fehler {resp.status_code}: {resp.text}"

# === Streamlit-UI ===
st.set_page_config(page_title="🤖 LLM-Debattenplattform", layout="wide")

def prompt_editor_ui():
    st.sidebar.markdown("### Konfigurationsprompt bearbeiten")
    template = load_prompt_template()
    edited = st.sidebar.text_area("Konfigurationsprompt (mit [SCHLAGWORT] als Platzhalter):", value=template, height=300)
    if st.sidebar.button("Prompt speichern"):
        save_prompt_template(edited)
        st.sidebar.success("Prompt gespeichert!")

version = st.selectbox("Version:", ["Grundversion", "Neu-Version"], index=0)
if st.sidebar.checkbox("Prompt bearbeiten (Admin)", value=False):
