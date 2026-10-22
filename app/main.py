import json
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader

load_dotenv()

MODEL = "gemini-3.8-flash"
MAX_CHARS = 15000

PROMPT = """Tu es un extracteur de CV. À partir du texte ci-dessous, réponds UNIQUEMENT
avec un objet JSON, sans texte autour, sans balises Markdown, respectant cette structure :
{
  "nom": "string ou null",
  "titre": "string ou null",
  "competences": ["string"],
  "experiences": [{"poste": "string", "entreprise": "string", "dates": "string", "missions": ["string"]}],
  "formations": [{"diplome": "string", "etablissement": "string", "annee": "string"}],
  "langues": ["string"]
}
Règle absolue : n'ajoute aucune information absente du texte.
Si une information manque, mets null ou une liste vide.

TEXTE DU CV :
"""


def extract_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def extract_profile(cv_text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY est absente. Vérifie ton fichier .env.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=PROMPT + cv_text[:MAX_CHARS],
        config={"response_mime_type": "application/json"},
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    return json.loads(raw)


st.set_page_config(page_title="Brieflyy", page_icon="📄")
st.title("Brieflyy : analyse de CV")
st.caption("Étape 1 : upload du CV et extraction du profil")

uploaded = st.file_uploader("Dépose ton CV (PDF)", type=["pdf"])

if uploaded and st.button("Analyser le CV"):
    with st.spinner("Lecture du CV et extraction du profil..."):
        try:
            text = extract_text(uploaded)
            if not text:
                st.error("Aucun texte lisible dans ce PDF. Vérifie qu'il n'est pas un scan image.")
            else:
                profile = extract_profile(text)
                st.success("Profil extrait.")
                st.json(profile)
                with st.expander("Texte brut extrait du PDF"):
                    st.text(text[:MAX_CHARS])
        except json.JSONDecodeError:
            st.error("Gemini n'a pas renvoyé un JSON valide. Relance l'analyse.")
        except Exception as e:
            st.error(f"Erreur : {e}")
