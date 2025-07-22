import streamlit as st
import time
import json

from api import debate_call
from prompt_utils import adjust_prompt_for_provider
from parsing import extract_json_fallback, show_debug_output

def run_grundversion():
    st.title("🤖 KI-Debattenplattform – Grundversion")
    st.subheader("Single-Call Debatte mit Fallback & Live-Statistiken")

    provider = st.radio("Modell-Anbieter wählen:", ["OpenAI (gpt-3.5-turbo)", "Groq (Mistral-saba-24b)"])
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
            base_prompt = (
                f"Thema: '{question}'\n"
                "Agent A (optimistisch)\nAgent B (pessimistisch)\n"
                "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
            )
        else:
            base_prompt = (
                f"Thema: '{question}'\n"
                "Agent A analysiert Chancen.\nAgent B analysiert Risiken.\n"
                "Bitte liefere als Ergebnis ein JSON mit den Feldern: optimistic, pessimistic, recommendation."
            )

        prompt = adjust_prompt_for_provider(base_prompt, provider)
        progress.progress(30)

        if provider.startswith("OpenAI"):
            api_url = "https://api.openai.com/v1/chat/completions"
            api_key = st.secrets.get("openai_api_key", "")
            model = "gpt-3.5-turbo"
            cost_rate = 0.002
        else:
            api_url = "https://api.groq.com/openai/v1/chat/completions"
            api_key = st.secrets.get("groq_api_key", "")
            model = "mistral-saba-24b"
            cost_rate = 0.0
        progress.progress(50)

        start_time = time.time()
        content, used = debate_call(provider, api_key, api_url, model, prompt)
        duration = time.time() - start_time
        if not content:
            st.error("Keine Antwort erhalten.")
            progress.progress(100)
            return

        raw = content.strip()
        if raw.startswith("```") and raw.endswith("```"):
            raw = "\n".join(raw.splitlines()[1:-1])

        if "{" in raw:
            try:
                data = json.loads(raw)
            except Exception:
                show_debug_output(raw)
                data = extract_json_fallback(raw)
        else:
            show_debug_output(raw)
            data = extract_json_fallback(raw)

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

version = st.selectbox("Version:", ["Grundversion"], index=0)
if version == "Grundversion":
    run_grundversion()

