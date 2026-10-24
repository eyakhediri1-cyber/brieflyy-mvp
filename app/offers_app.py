import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import base64
import hashlib
import streamlit.components.v1 as components
import json
from pathlib import Path

import streamlit as st

from app.adaptation import build_adapted_cv
from app.jobs import fetch_remotive_jobs
from app.cv import profile_from_pdf
from app.cv_pdf import render_cv_pdf

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Brieflyy - Job matches", page_icon="🎯", layout="wide")
st.title("Brieflyy: job matches")
st.caption("Offers come from the official Remotive API. Scores are produced by Gemini and by code, and may vary slightly between runs.")

with st.sidebar:
    st.header("1. Your CV")
    uploaded = st.file_uploader("Your CV (PDF)", type=["pdf"])
    demo_mode = st.checkbox("Demo mode (saved results only, no Gemini call)", value=False)
    st.header("2. Search")
    search = st.text_input("Job keywords", value="python")
    limit = st.slider("Number of offers", 1, 10, 3)

if not uploaded:
    st.info("Upload your CV (PDF) in the sidebar to start.")
    st.stop()

try:
    with st.spinner("Reading your CV..."):
        profile = profile_from_pdf(uploaded.getvalue())
except Exception as e:
    st.error(f"Could not read your CV: {e}")
    st.stop()



def cache_path(profile: dict, offer: dict) -> Path:
    key = json.dumps([profile, offer.get("url")], sort_keys=True, ensure_ascii=False)
    return CACHE_DIR / (hashlib.sha256(key.encode("utf-8")).hexdigest() + ".json")


def get_result(profile: dict, offer: dict):
    path = cache_path(profile, offer)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if demo_mode:
        return None
    result = build_adapted_cv(profile, offer)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def pct(value) -> str:
    return "n/a" if value is None else f"{value}%"


def cv_markdown(cv: dict) -> str:
    lines = [f"**{cv.get('titre') or ''}**", "", "**Skills:** " + ", ".join(cv.get("competences", [])), ""]
    for exp in cv.get("experiences", []):
        tag = " *(relevant)*" if exp.get("pertinente") else ""
        lines.append(f"**{exp.get('poste', '')}** at {exp.get('entreprise', '')} ({exp.get('dates', '')}){tag}")
        lines += [f"- {m}" for m in exp.get("missions", [])]
        lines.append("")
    return "\n".join(lines)


if st.button("Search offers"):
    try:
        st.session_state["offers"] = fetch_remotive_jobs(search, limit)
    except Exception as e:
        st.error(f"Could not load offers: {e}")

offers = st.session_state.get("offers", [])
if not offers:
    st.write("Click **Search offers** to load job offers.")
    st.stop()

for i, offer in enumerate(offers):
    with st.container(border=True):
        st.subheader(offer["title"])
        st.write(f"{offer['company']} · {offer['location']} · source: {offer['source']}")

        if st.button("Analyse my CV for this offer", key=f"btn_{i}"):
            with st.spinner("Analysing..."):
                try:
                    st.session_state[f"res_{i}"] = get_result(profile, offer)
                except Exception as e:
                    st.error(str(e))

        result = st.session_state.get(f"res_{i}")
        if result is None and demo_mode:
            st.warning("No saved result for this offer yet. Turn off demo mode to compute it.")
        elif result:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Match: original CV", pct(result["match_original"]))
            c2.metric("Match: adapted CV", pct(result["match_adapted"]))
            c3.metric("ATS: original CV", pct(result["ats_original"]["score"]))
            c4.metric("ATS: adapted CV", pct(result["ats_adapted"]["score"]))

            if result["ats_adapted"]["missing"]:
                st.write("**Keywords missing from your CV:** " + ", ".join(result["ats_adapted"]["missing"]))

            left, right = st.columns(2)
            with left:
                st.markdown("#### Original CV")
                st.markdown(cv_markdown(profile))
            with right:
                st.markdown("#### Adapted CV")
                st.markdown(cv_markdown(result["cv"]))
                st.caption(f"Missions rewritten: {result['report']['reformulees']} · kept as written: {result['report']['conservees']}")

        if result:
            pdf_bytes = render_cv_pdf(result["cv"], title=offer["title"])
            st.download_button(
                "Download adapted CV (PDF)",
                pdf_bytes,
                file_name=f"CV_adapted_{i + 1}.pdf",
                mime="application/pdf",
                key=f"dl_{i}",
            )
            with st.expander("Preview adapted CV"):
                b64 = base64.b64encode(pdf_bytes).decode("ascii")
                components.html(
                    f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700" style="border:none;"></iframe>',
                    height=720,
                )
        st.link_button("Apply on the original site", offer["url"])
