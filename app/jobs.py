import html
import re

import requests

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
SCAM_KEYWORDS = ["id verification", "vérification d'identité", "pay a fee", "frais d'inscription"]


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _looks_suspicious(description: str) -> bool:
    lowered = description.lower()
    return any(keyword in lowered for keyword in SCAM_KEYWORDS)


def fetch_remotive_jobs(search: str, limit: int = 10) -> list[dict]:
    response = requests.get(
        REMOTIVE_URL,
        params={"search": search, "limit": limit},
        timeout=15,
    )
    response.raise_for_status()

    jobs = []
    for job in response.json().get("jobs", []):
        description = _clean_html(job.get("description", ""))
        if _looks_suspicious(description):
            continue
        jobs.append({
            "source": "Remotive",
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("candidate_required_location", ""),
            "description": description[:4000],
            "url": job.get("url", ""),
            "published": job.get("publication_date", ""),
        })
    return jobs[:limit]
