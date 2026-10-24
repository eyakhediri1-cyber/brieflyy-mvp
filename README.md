# Brieflyy

**Brieflyy** is an AI-assisted career copilot for job seekers. Upload your CV (PDF), search live job offers, and get a match score, an ATS keyword check and a tailored CV, without invented content.

> Prototype developed for the CSTAM 3.0 Project Holders program (Phase 2). Initial idea developed at the USAII Global AI Hackathon 2026.

## What it does

1. **Reads your CV.** Extracts a structured profile (skills, experience, projects, education, languages) from a PDF with Gemini.
2. **Finds offers.** Searches live offers from the official Remotive and Adzuna APIs. Each offer links to its original listing.
3. **Scores the match.** Gives a match score for your current CV and for the adapted version, with strengths and gaps.
4. **Checks keywords (ATS).** Computes a keyword-coverage score for both versions and lists missing keywords. The score is calculated by code.
5. **Adapts your CV.** Reorders experiences and skills by relevance. A mission may be reworded only if the new wording adds no new number, tool or proper name. Otherwise the original sentence is kept.
6. **Exports a PDF.** Downloads the adapted CV, with a preview.

Brieflyy never sends an application on your behalf. You review each adapted CV and apply on the employer's site.

## Principles

- **No invented content.** The adapted CV only uses what is in your CV.
- **Transparent scores.** The fidelity check reports how many missions were reworded and how many were kept word for word.
- **Official data sources.** No scraping of sites whose terms forbid it.
- **You decide.** Nothing is sent to an employer without your action.

## Limitations

- Analyses depend on external AI services (Gemini, with a fallback provider). They can be temporarily overloaded. Computed analyses are cached locally.
- The ATS score measures keyword coverage only. It does not check PDF layout or parsing.
- The adapted score is often close to the original score, since the content is the same, reordered.
- The Adzuna account is on a trial plan, so live search volume is limited.
- Application tracking, interview preparation and automatic gap analysis for every offer are not built yet.

## Tech stack

- Python 3.10+
- Streamlit (interface)
- Google Gemini API (`google-genai`), with an OpenAI-compatible fallback (Groq)
- pypdf (text extraction), reportlab (PDF generation)
- Remotive API and Adzuna API (job offers)

## Installation

```bash
git clone https://github.com/eyakhediri1-cyber/brieflyy-mvp.git
cd brieflyy-mvp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your keys. Never commit this file:

```
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key        # optional, fallback provider
ADZUNA_APP_ID=your_adzuna_id      # optional, enables Adzuna offers
ADZUNA_APP_KEY=your_adzuna_key    # optional
```

## Run

```bash
python -m streamlit run app/offers_app.py --server.port 8502
```

Open http://localhost:8502, upload a PDF CV, then search offers.

## Project structure

```
app/
  offers_app.py   Streamlit interface
  cv.py           CV text extraction and profile
  cv_pdf.py       Adapted CV PDF generation
  adaptation.py   Reordering, faithfulness check, ATS score
  scoring.py      Match score (strengths, gaps)
  jobs.py         Remotive and Adzuna clients
  llm.py          AI calls with provider fallback
```

## Author

Eya Khediri, developer of this CSTAM prototype.

## License

MIT. See [LICENSE](LICENSE).