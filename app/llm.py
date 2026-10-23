import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()

# Essayés dans l'ordre : si l'un est saturé (503) ou limité (429), on passe au suivant
MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash"]
ATTEMPTS_PER_MODEL = 2


def generate_json(prompt: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY est absente. Vérifie ton fichier .env.")

    client = genai.Client(api_key=api_key)
    last_error = None
    for model in MODELS:
        for _ in range(ATTEMPTS_PER_MODEL):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
            except APIError as e:
                last_error = e
                if e.code not in (429, 503):
                    raise  # erreur réelle (clé, modèle inexistant) : inutile de réessayer
                time.sleep(3)
                continue

            raw = (response.text or "").strip()
            if raw.startswith("```"):
                raw = raw.strip("`").removeprefix("json").strip()
            return json.loads(raw)

    raise RuntimeError(f"Tous les modèles sont saturés, réessaie dans quelques minutes. ({last_error})")
