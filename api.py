import requests
import time
import streamlit as st

def debate_call(selected_provider, api_key, api_url, model, prompt, timeout=25):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 200
    }
    while True:
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            st.error(f"Verbindungsfehler: {e}")
            return None, selected_provider

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

