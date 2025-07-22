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
