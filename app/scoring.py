import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = "gemini-3.5-flash"  # même valeur que dans app/main.py

PROMPT = """Tu compares le profil d'un candidat à une offre d'emploi.
Réponds UNIQUEMENT avec un objet JSON, sans texte autour, sans balises Markdown, avec cette structure :
{
  "score": nombre entier de 0 à 100,
  "strengths": ["string"],
  "gaps": ["string"],
  "explanation": "string"
}
Règles absolues :
- "strengths" : compétences ou expériences du profil qui répondent à l'offre.
- "gaps" : exigences de l'offre absentes du profil.
- Ne cite que des éléments présents dans le profil ou l'offre. N'invente rien.
- "explanation" : 2 à 3 phrases qui justifient le score en citant le profil réel.
- Le score doit refléter les compétences et l'expérience, pas la seule présence de mots-clés.

PROFIL DU CANDIDAT :
PROFILE_JSON

OFFRE :
OFFER_JSON
"""


def score_offer(profile: dict, offer: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY est absente. Vérifie ton fichier .env.")

    offer_data = {
        "titre": offer.get("title"),
        "entreprise": offer.get("company"),
        "lieu": offer.get("location"),
        "description": (offer.get("description") or "")[:4000],
    }

    prompt = (
        PROMPT
        .replace("PROFILE_JSON", json.dumps(profile, ensure_ascii=False, indent=2))
        .replace("OFFER_JSON", json.dumps(offer_data, ensure_ascii=False, indent=2))
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    result = json.loads(raw)
    result["score"] = max(0, min(100, int(result.get("score", 0))))
    return result
