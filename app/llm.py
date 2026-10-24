import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from openai import OpenAI

load_dotenv()

GEMINI_MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]
RETRYABLE = (429, 503, 504)


def _parse(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    return json.loads(raw)


def _gemini(prompt: str) -> dict:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options={"timeout": 30000})
    last = None
    for model in GEMINI_MODELS:
        try:
            r = client.models.generate_content(
                model=model,
                contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0},
            )
            return _parse(r.text)
        except APIError as e:
            last = e
            if e.code in RETRYABLE:
                continue
            raise
        except Exception as e:
            last = e
    raise RuntimeError(f"Gemini indisponible : {last}")


def _grok(prompt: str) -> dict:
    client = OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1", timeout=30)
    r = client.chat.completions.create(
        model="grok-3-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return _parse(r.choices[0].message.content)


def _groq(prompt: str) -> dict:
    client = OpenAI(api_key=os.environ["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1", timeout=30)
    r = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return _parse(r.choices[0].message.content)


def _providers():
    """Fournisseurs dans l'ordre d'essai. Groq n'est utilisé que si sa clé est présente."""
    yield "gemini", _gemini
    if os.getenv("GROQ_API_KEY"):
        yield "groq", _groq


def generate_json(prompt: str) -> dict:
    errors = []
    for name, call in _providers():
        try:
            return call(prompt)
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise RuntimeError("Tous les fournisseurs ont échoué. " + " | ".join(errors))
