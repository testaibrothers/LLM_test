import re
import streamlit as st

def extract_json_fallback(text):
    optimistic = re.search(r'optimistic\\W+(.*?)\\n', text, re.IGNORECASE | re.DOTALL)
    pessimistic = re.search(r'pessimistic\\W+(.*?)\\n', text, re.IGNORECASE | re.DOTALL)
    recommendation = re.search(r'recommendation\\W+(.*?)\\n', text, re.IGNORECASE | re.DOTALL)
    return {
        "optimistic": optimistic.group(1).strip() if optimistic else "-",
        "pessimistic": pessimistic.group(1).strip() if pessimistic else "-",
        "recommendation": recommendation.group(1).strip() if recommendation else "-"
    }

def show_debug_output(raw):
    st.warning("Antwort nicht als JSON erkennbar. Roh-Antwort folgt:")
    st.code(raw, language="text")

