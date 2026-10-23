import copy
import json
import re

from app.llm import generate_json
from app.scoring import score_offer

PROMPT = """Tu prépares un CV pour une offre d'emploi. Tu ne fais que TRIER et REFORMULER ce qui existe déjà.
Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, sans balises Markdown :
{
  "offer_keywords": ["string"],
  "skills_order": [entiers],
  "experiences": [
    {"index": entier, "relevant": true ou false,
     "missions": [{"source": entier, "text": "string ou null"}]}
  ]
}
Règles absolues :
- "offer_keywords" : 10 à 20 compétences, outils ou exigences techniques cités explicitement dans l'offre.
- "skills_order" : indices de "competences", du plus pertinent pour l'offre au moins pertinent. N'en omets aucun.
- "experiences" : indices de "experiences", les plus pertinentes d'abord. "relevant" vaut false si l'expérience n'a aucun lien avec l'offre.
- "missions" : "source" est l'indice de la mission d'origine. "text" est une reformulation courte qui met en avant les termes de l'offre SEULEMENT si ces termes correspondent déjà à la mission.
- Interdit : ajouter un chiffre, un outil, une technologie, une entreprise, un diplôme, une date ou une responsabilité absents de la mission d'origine. Ne supprime jamais un chiffre ou un outil.
- Si une mission n'a aucun rapport avec l'offre, mets "text" à null.

PROFIL (avec indices) :
PROFILE_JSON

OFFRE :
OFFER_JSON
"""


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _strings(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _strings(item)


def _mentions(text: str, term: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"
    return re.search(pattern, text.lower()) is not None


def _proper_tokens(text: str) -> set[str]:
    """Nombres, sigles et mots avec majuscule (outils, noms propres)."""
    found = set(re.findall(r"\d[\d.,%]*", text))
    found |= {m.lower() for m in re.findall(r"(?<=\s)[A-Z][\w+#.\-]*", text)}
    found |= {m.lower() for m in re.findall(r"\b[A-Z]{2,}\b", text)}
    return found


def is_faithful(new_text: str, source_text: str, terms: list[str]) -> bool:
    """Vrai si la reformulation n'ajoute aucun nombre, nom propre ni terme absent de la source."""
    if not _proper_tokens(new_text) <= _proper_tokens(source_text):
        return False
    for term in terms:
        if _mentions(new_text, term) and not _mentions(source_text, term):
            return False
    return True


def _perm(order, size: int) -> list[int]:
    """Indices valides dans l'ordre proposé, puis les indices absents dans l'ordre d'origine."""
    seen = []
    for i in order if isinstance(order, list) else []:
        if isinstance(i, int) and not isinstance(i, bool) and 0 <= i < size and i not in seen:
            seen.append(i)
    return seen + [i for i in range(size) if i not in seen]


def _call_model(profile: dict, offer: dict) -> dict:
    indexed = {
        "competences": [{"index": i, "valeur": s} for i, s in enumerate(profile.get("competences") or [])],
        "experiences": [
            {
                "index": i,
                "poste": e.get("poste"),
                "entreprise": e.get("entreprise"),
                "missions": [{"index": j, "valeur": m} for j, m in enumerate(e.get("missions") or [])],
            }
            for i, e in enumerate(profile.get("experiences") or [])
        ],
    }
    offer_data = {
        "titre": offer.get("title"),
        "entreprise": offer.get("company"),
        "description": (offer.get("description") or "")[:4000],
    }
    prompt = (
        PROMPT
        .replace("PROFILE_JSON", json.dumps(indexed, ensure_ascii=False, indent=2))
        .replace("OFFER_JSON", json.dumps(offer_data, ensure_ascii=False, indent=2))
    )
    return generate_json(prompt)


def _rewrite_missions(source_missions: list, item: dict, terms: list[str]):
    proposed = {}
    for m in (item or {}).get("missions") or []:
        if isinstance(m, dict) and isinstance(m.get("source"), int) and 0 <= m["source"] < len(source_missions):
            proposed.setdefault(m["source"], m.get("text"))

    result = []
    report = {"reformulees": 0, "conservees": 0}
    for s in _perm(list(proposed.keys()), len(source_missions)):
        text = proposed.get(s)
        if isinstance(text, str) and text.strip() and is_faithful(text, source_missions[s], terms):
            result.append(text.strip())
            report["reformulees"] += 1
        else:
            result.append(source_missions[s])
            report["conservees"] += 1
    return result, report


def adapt_cv(profile: dict, offer: dict):
    """Retourne (CV adapté, rapport, mots-clés de l'offre)."""
    skills = profile.get("competences") or []
    exps = profile.get("experiences") or []

    try:
        data = _call_model(profile, offer)
    except (ValueError, KeyError, TypeError, RuntimeError):
        data = {}  # réponse inexploitable : on garde l'ordre d'origine
    if not isinstance(data, dict):
        data = {}

    keywords = [k.strip() for k in (data.get("offer_keywords") or []) if isinstance(k, str) and k.strip()]
    terms = [s for s in skills if isinstance(s, str)] + keywords

    adapted = copy.deepcopy(profile)
    adapted["competences"] = [skills[i] for i in _perm(data.get("skills_order"), len(skills))]

    proposed = {}
    for item in data.get("experiences") or []:
        if isinstance(item, dict) and isinstance(item.get("index"), int) and not isinstance(item.get("index"), bool):
            proposed.setdefault(item["index"], item)

    keep = [i for i in proposed if 0 <= i < len(exps) and proposed[i].get("relevant") is True]
    rest = [i for i in range(len(exps)) if i not in keep]  # sans rapport ou non citées : en dernier

    report = {"reformulees": 0, "conservees": 0}
    new_exps = []
    for i in keep + rest:
        exp = copy.deepcopy(exps[i])
        exp["pertinente"] = i in keep
        missions, r = _rewrite_missions(exps[i].get("missions") or [], proposed.get(i), terms)
        exp["missions"] = missions
        report["reformulees"] += r["reformulees"]
        report["conservees"] += r["conservees"]
        new_exps.append(exp)
    adapted["experiences"] = new_exps

    return adapted, report, keywords


def ats_report(cv: dict, keywords: list[str]) -> dict:
    """Score ATS = part des mots-clés de l'offre présents dans le CV. Calcul déterministe."""
    text = " ".join(_strings(cv))
    keywords = list(dict.fromkeys(keywords))
    matched = [k for k in keywords if _mentions(text, k)]
    missing = [k for k in keywords if k not in matched]
    score = round(100 * len(matched) / len(keywords)) if keywords else None
    return {"score": score, "matched": matched, "missing": missing}


def build_adapted_cv(profile: dict, offer: dict) -> dict:
    adapted, report, keywords = adapt_cv(profile, offer)
    return {
        "cv": adapted,
        "report": report,
        "keywords": keywords,
        "ats_original": ats_report(profile, keywords),
        "ats_adapted": ats_report(adapted, keywords),
        "match_original": score_offer(profile, offer)["score"],
        "match_adapted": score_offer(adapted, offer)["score"],
    }
