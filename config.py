PROVIDERS = ["OpenAI (gpt-3.5-turbo)", "Groq (Mistral-saba-24b)"]
USE_CASES = ["Allgemeine Diskussion", "SaaS Validator", "SWOT Analyse", "Pitch-Kritik", "WLT Entscheidung"]
LLM_LIST = ["gpt-3.5-turbo", "gpt-4", "claude-3", "mistral-saba-24b", "llama-2-13b"]

def get_api_conf(provider):
    import streamlit as st
    if provider.startswith("OpenAI"):
        return "https://api.openai.com/v1/chat/completions", st.secrets.get("openai_api_key", ""), "gpt-3.5-turbo", 0.002
    else:
        return "https://api.groq.com/openai/v1/chat/completions", st.secrets.get("groq_api_key", ""), "mistral-saba-24b", 0.0
