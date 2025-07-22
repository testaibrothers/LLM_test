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
        # === DEBUG 1: Prompt anzeigen ===
        st.text_area("DEBUG: Prompt an LLM", prompt, height=100)
        progress.progress(30)
        api_url, api_key, model, cost_rate = get_api_conf(provider)
        progress.progress(50)
        start_time = time.time()
        content, used = debate_call(provider, api_key, api_url, model, prompt)
        duration = time.time() - start_time
        # === DEBUG 2: Raw-Response anzeigen ===
        st.text_area("DEBUG: RAW-Response vom LLM", content or "", height=150)
        if not content:
            st.error("Keine Antwort erhalten.")
            progress.progress(100)
            st.stop()
        data, raw = parse_json_response(content)
        # === DEBUG 3: Nach Parsing anzeigen ===
        st.text_area("DEBUG: Nach Parsing (raw)", raw or "", height=150)
        st.text_area("DEBUG: Nach Parsing (data)", str(data) or "", height=150)
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
