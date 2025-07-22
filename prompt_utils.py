def adjust_prompt_for_provider(prompt: str, provider: str) -> str:
    if "Groq" in provider:
        return (
            "Du bist ein präziser JSON-Antwortgenerator. Antworte nie mit Fließtext oder Code. "
            "Deine einzige Ausgabe ist folgendes JSON: "
            "{\"optimistic\":\"...\", \"pessimistic\":\"...\", \"recommendation\":\"...\"}. "
            "Gib kein Markdown, keine Einleitung, keine Erklärungen aus. Nur reines, minimales JSON.\n" + prompt
        )
    return prompt
