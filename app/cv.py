import hashlib
import io
import json
import os

from dotenv import load_dotenv
from pypdf import PdfReader

from app.llm import generate_json

load_dotenv()

MAX_CHARS = 15000

PROMPT = """Tu es un extracteur de CV FIDÈLE. À partir du texte ci-dessous, réponds UNIQUEMENT
avec un objet JSON valide, sans texte autour, sans balises Markdown, avec cette structure :
{
  "nom": "string ou null",
  "titre": "string ou null",
  "email": "string ou null",
  "ville": "string ou null",
  "linkedin": "string ou null",
  "github": "string ou null",
  "profil": "string ou null",
  "competences": ["string"],
  "experiences": [{"poste": "string", "entreprise": "string", "dates": "string", "missions": ["string"]}],
  "projets": [{"nom": "string", "dates": "string ou null", "description": ["string"], "lien": "string ou null"}],
  "formations": [{"diplome": "string", "etablissement": "string", "annee": "string", "details": ["string"]}],
  "associations": [{"nom": "string", "role": "string ou null", "dates": "string ou null"}],
  "certifications": ["string"],
  "langues": ["string"]
}
Règles absolues :
- Recopie TOUT ce qui figure dans le CV : chaque section, chaque projet, chaque association, chaque formation.
- Recopie les textes mot pour mot. Ne résume pas, ne reformule pas, ne supprime aucun élément.
- N'ajoute aucune information absente du texte. Si une information manque, mets null ou une liste vide.
- Les coordonnées (email, ville, liens) sont recopiées telles qu'elles apparaissent.

TEXTE DU CV :
"""


def extract_text(pdf_file) -> str:
    reader = PdfReader(pdf_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def extract_profile(cv_text: str) -> dict:
    return generate_json(PROMPT + cv_text[:MAX_CHARS])


def profile_from_pdf(pdf_bytes: bytes) -> dict:
    """Extrait le profil d'un PDF. Résultat mis en cache par empreinte du fichier."""
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    cache = os.path.join("data", "cache", f"profile_{digest}.json")
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            return json.load(f)

    text = extract_text(io.BytesIO(pdf_bytes))
    if not text:
        raise ValueError("Aucun texte lisible dans ce PDF (scan image ?).")
    profile = extract_profile(text)

    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    return profile
