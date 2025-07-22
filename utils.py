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
