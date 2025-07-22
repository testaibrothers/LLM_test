# LLM-Debate Plattform (MVP) – Bugfix 23.07.2025
# Modular, 1 File pro Modul, robust importierbar

# === main.py ===
import streamlit as st
from api import debate_call, generate_prompt_grok
from config import PROVIDERS, USE_CASES, LLM_LIST
from utils import parse_json_response, load_prompt_template, save_prompt_template, build_final_prompt

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
    prompt_editor_ui()

if version == "Grundversion":
    st.title("🤖 KI-Debattenplattform – Grundversion")
    st.subheader("Single-Call Debatte mit Fallback & Live-Statistiken")
    provider = st.radio("Modell-Anbieter wählen:", PROVIDERS)
    use_case = st.selectbox("Use Case auswählen:", USE_CASES, index=0)
    question = st.text_area("Deine Fragestellung:")
    start = st.button("Debatte starten")
    if start and question:
        progress = st.progress(0)
        st.info("Debatte läuft...")
        progress.progress(10)
        if use_case == "Allgemeine Diskussion":
            prompt = f"Simuliere eine Debatte zwischen zwei KI-Agenten zum Thema: '{question}'\nAgent A (optimistisch)\nAgent B (pessimistisch)\nAntwort als JSON mit Feldern: optimistic, pessimistic, recommendation"
        else:
            prompt = f"Simuliere Debatte zum Use Case '{use_case}': Thema: '{question}'\nAgent A analysiert Chancen.\nAgent B analysiert Risiken.\nAntwort als JSON: optimistic, pessimistic, recommendation"
        progress.progress(30)
        from config import get_api_conf
        api_url, api_key, model, cost_rate = get_api_conf(provider)
        progress.progress(50)
        import time
        start_time = time.time()
        content, used = debate_call(provider, api_key, api_url, model, prompt)
        duration = time.time() - start_time
        if not content:
            st.error("Keine Antwort erhalten.")
            progress.progress(100)
            st.stop()
        data, raw = parse_json_response(content)
        progress.progress(70)
        st.markdown(f"**Provider:** {used}")
        if used.startswith("OpenAI"):
            tokens = len(raw.split())
            st.markdown(f"**Kosten:** ${(tokens/1000)*cost_rate:.4f}")
        st.markdown(f"**Dauer:** {duration:.2f}s")
        progress.progress(90)
        st.markdown("### 🤝 Optimistische Perspektive")
        st.write(data.get("optimistic", "-"))
        st.markdown("### ⚠️ Pessimistische Perspektive")
        st.write(data.get("pessimistic", "-"))
        st.markdown("### ✅ Empfehlung")
        st.write(data.get("recommendation", "-"))
        progress.progress(100)
else:
    st.title("🤖 KI-Debattenplattform – Neu-Version")
    col1, col2 = st.columns(2)
    with col1:
        agent_a_model = st.selectbox("Agent A LLM:", LLM_LIST, key="neu_a")
    with col2:
        agent_b_model = st.selectbox("Agent B LLM:", LLM_LIST, key="neu_b")
    st.markdown("### Agenteinstellung")
    mode = st.radio("Einstellung:", ["Prompt", "Charakter"], key="mode_neu")
    if "pA_neu" not in st.session_state:
        st.session_state["pA_neu"] = ""
    if "pB_neu" not in st.session_state:
        st.session_state["pB_neu"] = ""
    if mode == "Prompt":
        with st.sidebar.expander("Prompt-Generator (optional)", expanded=False):
            st.markdown("**Prompt-Konfiguration:** Dein System-Prompt aus prompt_template.txt mit [SCHLAGWORT].")
            schlagwort = st.text_input("Schlagwort für den Prompt:", key="gen_kw")
            if st.button("Generiere Prompt", key="gen_btn") and schlagwort:
                prompt_gen = build_final_prompt(schlagwort)
                gen_response = generate_prompt_grok(prompt_gen)
                st.text_area("Generierter Prompt:", value=gen_response, height=150, key="gen_out")
                a, b = st.columns(2)
                with a:
                    if st.button("In Prompt A übernehmen", key="toA"):
                        st.session_state["pA_neu"] = gen_response
                with b:
                    if st.button("In Prompt B übernehmen", key="toB"):
                        st.session_state["pB_neu"] = gen_response
        diff = st.checkbox("Unterschiedliche Prompts für A und B", key="diff_neu")
        if diff:
            prompt_a = st.text_area("Prompt für Agent A", value=st.session_state["pA_neu"], key="pA_neu")
            prompt_b = st.text_area("Prompt für Agent B", value=st.session_state["pB_neu"], key="pB_neu")
        else:
            shared = st.text_area("Gemeinsamer Prompt (optional)", value=st.session_state.get("shared_same", ""), key="shared_same")
            prompt_a = prompt_b = shared
    else:
        opts = ["Optimistisch", "Pessimistisch", "Kritisch"]
        c1, c2 = st.columns(2)
        with c1:
            char_a = st.selectbox("Agent A:", opts, key="cA_neu")
        with c2:
            char_b = st.selectbox("Agent B:", opts, key="cB_neu")
        prompt_a = f"Du bist Agent A und agierst {char_a.lower()}."
        prompt_b = f"Du bist Agent B und agierst {char_b.lower()}."
    question_neu = st.text_area("Deine Frage:", key="q_neu")
    if st.button("Diskussion starten", key="start_neu") and question_neu:
        st.markdown(f"**Modelle:** A={agent_a_model}, B={agent_b_model}")
        combined_a = prompt_a + "\n" + question_neu
        combined_b = prompt_b + "\n" + question_neu
        from config import get_api_conf
        api_url, api_key, _, _ = get_api_conf("OpenAI (gpt-3.5-turbo)")
        resp_a, _ = debate_call("OpenAI", api_key, api_url, agent_a_model, combined_a)
        resp_b, _ = debate_call("OpenAI", api_key, api_url, agent_b_model, combined_b)
        st.markdown("### 🗣️ Agent A Antwort")
        st.write(resp_a)
        st.markdown("### 🗣️ Agent B Antwort")
        st.write(resp_b)

# === utils.py ===
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
    import json
    raw = content.strip()
    if raw.startswith("```") and raw.endswith("```"):
        raw = "\n".join(raw.splitlines()[1:-1])
    try:
        data = json.loads(raw)
    except:
        data = {}
    return data, raw

# === api.py ===
import requests
import streamlit as st

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
            import time
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

# === config.py ===
PROVIDERS = ["OpenAI (gpt-3.5-turbo)", "Groq (Mistral-saba-24b)"]
USE_CASES = ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"]
LLM_LIST = ["gpt-3.5-turbo", "gpt-4", "claude-3", "mistral-saba-24b", "llama-2-13b"]

def get_api_conf(provider):
    import streamlit as st
    if provider.startswith("OpenAI"):
        return "https://api.openai.com/v1/chat/completions", st.secrets.get("openai_api_key", ""), "gpt-3.5-turbo", 0.002
    else:
        return "https://api.groq.com/openai/v1/chat/completions", st.secrets.get("groq_api_key", ""), "mistral-saba-24b", 0.0
