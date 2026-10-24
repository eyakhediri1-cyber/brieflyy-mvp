
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import base64
import hashlib
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.adaptation import build_adapted_cv
from app.cv import profile_from_pdf
from app.cv_pdf import render_cv_pdf
from app.jobs import fetch_adzuna_jobs, fetch_remotive_jobs

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
PRIMARY = "#263A8B"

st.set_page_config(
    page_title="Brieflyy — Career Copilot",
    page_icon="B",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Visual design only: no changes to the app's business logic ────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
      --ink: #172033;
      --muted: #667085;
      --brand: #263A8B;
      --brand-2: #5368E8;
      --line: #E7EAF2;
      --surface: #FFFFFF;
      --wash: #F5F7FC;
    }

    html, body, [class*="css"] {
      font-family: 'DM Sans', sans-serif;
      color: var(--ink);
    }
    .stApp {
      background:
        radial-gradient(ellipse at 85% 0%, rgba(117, 133, 255, .10), transparent 30%),
        linear-gradient(180deg, #F8F9FD 0%, #F5F7FC 100%);
    }
    .block-container {
      max-width: 1440px;
      padding-top: 1.6rem;
      padding-bottom: 3.5rem;
    }
    h1, h2, h3, h4 {
      font-family: 'Manrope', sans-serif !important;
      color: #172033;
      letter-spacing: -.035em;
    }
    h1 { font-weight: 800 !important; }
    h2, h3, h4 { font-weight: 750 !important; }
    p, label, .stMarkdown { color: #344054; }

    /* Sidebar */
    [data-testid="stSidebar"] {
      background: #fff;
      border-right: 1px solid #E7EAF2;
    }
    [data-testid="stSidebar"] > div:first-child {
      padding-top: 1.25rem;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
      font-size: .92rem;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
      letter-spacing: -.025em;
    }

    /* Hero */
    .brand-row {
      display: flex; align-items: center; gap: 12px;
      margin: 0 0 1.3rem 0;
    }
    .brand-mark {
      display: grid; place-items: center;
      width: 46px; height: 46px; border-radius: 15px;
      color: white; font-size: 23px;
      background: linear-gradient(135deg, #263A8B 0%, #6878F4 100%);
      box-shadow: 0 8px 22px rgba(56, 74, 177, .22);
    }
    .brand-name {
      font: 800 1.42rem 'Manrope', sans-serif;
      letter-spacing: -.05em; color: #172033; line-height: 1.1;
    }
    .brand-sub {
      color: #7A8499; font-size: .78rem; margin-top: 3px;
    }
    .hero {
      position: relative; overflow: hidden;
      padding: 34px 36px;
      border-radius: 26px;
      color: white;
      background: linear-gradient(115deg, #1D2C68 0%, #303F9F 54%, #5969E8 100%);
      box-shadow: 0 18px 45px rgba(39, 55, 139, .18);
      margin-bottom: 1.35rem;
    }
    .hero:after {
      content: ''; position: absolute; width: 310px; height: 310px;
      right: -75px; top: -155px; border-radius: 50%;
      border: 1px solid rgba(255,255,255,.15);
      box-shadow: 0 0 0 35px rgba(255,255,255,.035), 0 0 0 75px rgba(255,255,255,.025);
    }
    .hero-eyebrow {
      display: inline-flex; align-items: center; gap: 7px;
      border: 1px solid rgba(255,255,255,.22);
      background: rgba(255,255,255,.10);
      padding: 6px 11px; border-radius: 999px;
      color: #E5E9FF; font-size: .76rem; font-weight: 700;
      letter-spacing: .04em; text-transform: uppercase;
    }
    .hero h1 {
      color: white !important; font-size: clamp(1.9rem, 3vw, 2.7rem) !important;
      line-height: 1.15; margin: 16px 0 10px 0;
      max-width: 760px;
    }
    .hero p {
      color: #E0E5FF !important; font-size: 1.02rem;
      max-width: 680px; line-height: 1.65; margin: 0;
    }
    .hero-note {
      margin-top: 20px; color: #D9E0FF; font-size: .8rem;
    }

    /* Section headings and small labels */
    .section-kicker {
      color: #6674C9; text-transform: uppercase;
      font-size: .73rem; font-weight: 800; letter-spacing: .12em;
      margin-bottom: 5px;
    }
    .section-title {
      font: 800 1.45rem 'Manrope', sans-serif;
      letter-spacing: -.045em; color: #172033; margin-bottom: 4px;
    }
    .section-desc { color: #7A8499; font-size: .92rem; margin-bottom: 1rem; }
    .soft-card {
      background: rgba(255,255,255,.92);
      border: 1px solid #E7EAF2;
      border-radius: 18px; padding: 20px 22px;
      box-shadow: 0 5px 18px rgba(26, 39, 82, .035);
    }
    .step-card {
      background: white; border: 1px solid #E7EAF2;
      border-radius: 17px; padding: 17px 18px; min-height: 118px;
      box-shadow: 0 4px 16px rgba(26, 39, 82, .025);
    }
    .step-number {
      display: inline-grid; place-items: center;
      width: 30px; height: 30px; border-radius: 10px;
      color: #3546A5; background: #EEF0FF;
      font-weight: 800; font-size: .85rem; margin-bottom: 11px;
    }
    .step-title { color: #202A43; font-weight: 800; font-size: .92rem; }
    .step-copy { color: #7A8499; font-size: .8rem; line-height: 1.5; margin-top: 5px; }

    /* Job cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
      border: 1px solid #E5E9F3 !important;
      border-radius: 20px !important;
      background: rgba(255,255,255,.95) !important;
      box-shadow: 0 7px 24px rgba(30, 42, 85, .045);
      transition: border-color .18s ease, box-shadow .18s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
      border-color: #C9D0F7 !important;
      box-shadow: 0 12px 30px rgba(30, 42, 85, .075);
    }
    .job-label {
      display: inline-flex; align-items: center;
      background: #EEF0FF; color: #3949AB;
      border: 1px solid #E0E4FF;
      padding: 5px 10px; border-radius: 999px;
      font-size: .73rem; font-weight: 800;
    }
    .job-subtitle { color: #737E94; font-size: .88rem; margin-top: -7px; }
    .badge {
      display: inline-block; padding: 4px 10px; border-radius: 999px;
      background: #EEF0FF; color: #3446A4; font-size: .75rem;
      font-weight: 700; margin: 2px 4px 2px 0;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea {
      border-radius: 12px !important;
      border-color: #DDE2EE !important;
      background: white !important;
    }
    [data-testid="stFileUploader"] {
      border: 1px dashed #B9C3E7;
      border-radius: 15px;
      background: #F8F9FF;
      padding: 8px;
    }
    [data-testid="stFileUploader"] section {
      border: 0 !important;
    }
    .stButton > button, .stDownloadButton > button, .stLinkButton > a {
      border-radius: 12px !important;
      min-height: 43px;
      font-weight: 750 !important;
      transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button[kind="primary"] {
      background: linear-gradient(135deg, #3446A4, #6574EF) !important;
      border: 0 !important;
      color: white !important;
      box-shadow: 0 7px 16px rgba(65, 80, 190, .18);
    }
    .stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {
      transform: translateY(-1px);
      box-shadow: 0 7px 16px rgba(30, 42, 85, .10);
    }
    .stLinkButton > a {
      border: 1px solid #DCE1EF !important;
      color: #344054 !important;
      background: #fff !important;
    }

    /* Metrics and tabs */
    [data-testid="stMetric"] {
      background: #F8F9FE;
      border: 1px solid #E9ECF6;
      padding: 15px 16px;
      border-radius: 15px;
    }
    [data-testid="stMetricLabel"] { color: #737E94 !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #263A8B !important; font-weight: 800; }
    .stTabs [data-baseweb="tab-list"] {
      gap: 8px; border-bottom: 1px solid #E7EAF2;
    }
    .stTabs [data-baseweb="tab"] {
      background: transparent; border-radius: 10px 10px 0 0;
      padding: 10px 15px; font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
      color: #3446A4 !important;
      border-bottom-color: #5368E8 !important;
    }
    [data-testid="stAlert"] { border-radius: 13px; }
    hr { border-color: #E7EAF2 !important; }
    footer { visibility: hidden; }

    /* Hide Streamlit's developer toolbar and Deploy prompt for a cleaner app UI.
       This is a visual CSS hide; Streamlit may change these selectors between versions. */
    /* Hide only the Deploy prompt; keep Streamlit navigation controls available. */
    [data-testid="stDeployButton"] { display: none !important; visibility: hidden !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    /* Keep the header and sidebar collapse/expand button visible. */
    header[data-testid="stHeader"] { background: transparent !important; visibility: visible !important; display: flex !important; }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"] { display: flex !important; visibility: visible !important; opacity: 1 !important; }
    /* Sidebar stays available on the workspace screen. */
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] { display: block !important; visibility: visible !important; }

    /* Cinematic landing page inspired by the supplied premium SaaS reference */
    /* True edge-to-edge landing: no centered card, no browser-like frame */
    .stApp:has(.landing-shell) { background:#07070B; overflow:hidden; }
    .stApp:has(.landing-shell) [data-testid="stToolbar"],
    .stApp:has(.landing-shell) [data-testid="stDecoration"] { display:none !important; }
    .stApp:has(.landing-shell) [data-testid="stSidebar"] { display:none !important; }
    .stApp:has(.landing-shell) .main,
    .stApp:has(.landing-shell) [data-testid="stAppViewContainer"],
    .stApp:has(.landing-shell) [data-testid="stMain"] { padding:0 !important; margin:0 !important; }
    .stApp:has(.landing-shell) .block-container { max-width:none !important; width:100% !important; padding:0 !important; margin:0 !important; }
    .stApp:has(.landing-shell) .block-container > div { gap:0 !important; }
    .landing-shell { position:fixed; inset:0; z-index:9999; width:100vw; height:100vh; height:100dvh; min-height:100vh; overflow:hidden; isolation:isolate; border:0; border-radius:0; background:#09090D; box-shadow:none; }
    .landing-video { position:absolute; z-index:-2; inset:0; width:100%; height:100%; object-fit:cover; opacity:.60; }
    .landing-overlay { position:absolute; z-index:-1; inset:0; background:linear-gradient(180deg,rgba(5,5,9,.82) 0%,rgba(5,5,9,.48) 35%,rgba(22,11,40,.12) 68%,rgba(5,5,9,.72) 100%),linear-gradient(90deg,rgba(5,5,9,.38),transparent 50%,rgba(5,5,9,.22)); }
    .landing-nav { display:flex; align-items:center; justify-content:space-between; gap:20px; padding:22px clamp(22px,4vw,54px); border-bottom:1px solid rgba(255,255,255,.09); background:rgba(8,8,12,.48); backdrop-filter:blur(16px); }
    .landing-brand { display:flex; align-items:center; gap:11px; }
    .landing-mark { display:grid; place-items:center; width:38px; height:38px; border-radius:12px; background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.28); color:white; font:800 21px 'Manrope',sans-serif; letter-spacing:-2px; }
    .landing-brand-name { color:#fff; font:800 1.25rem 'Manrope',sans-serif; letter-spacing:-.05em; }
    .landing-brand-sub { color:#C4CCE8; font-size:.72rem; margin-top:1px; }
    .landing-nav-links { display:flex; align-items:center; gap:clamp(12px,2vw,28px); color:#E5E5EC; font-size:.78rem; }
    .landing-nav-links span:last-child { border:1px solid rgba(163,112,255,.8); border-radius:9px; padding:10px 14px; box-shadow:0 0 18px rgba(124,58,237,.18); }
    .landing-content { position:relative; z-index:2; text-align:center; max-width:1000px; margin:0 auto; padding:clamp(70px,12vh,140px) 24px 145px; }
    .landing-eyebrow { display:inline-block; color:#D8C7FF; font-size:.72rem; font-weight:800; text-transform:uppercase; letter-spacing:.16em; border:1px solid rgba(193,164,255,.30); background:rgba(94,49,154,.18); padding:8px 13px; border-radius:999px; }
    .landing-title { color:#fff !important; font:600 clamp(2.35rem,5.2vw,4.6rem)/1.08 'Manrope',sans-serif !important; letter-spacing:-.06em; margin:22px auto 18px; max-width:850px; }
    .landing-title span { background:linear-gradient(100deg,#B7A0FF,#8C69F4,#D5B7FF); -webkit-background-clip:text; background-clip:text; color:transparent; }
    .landing-copy { color:#D0CFDA; font-size:clamp(.94rem,1.25vw,1.08rem); line-height:1.75; max-width:660px; margin:0 auto; }
    .landing-proof { display:flex; justify-content:center; flex-wrap:wrap; gap:10px 22px; color:#E1DDEB; font-size:.78rem; margin-top:24px; }
    .landing-foot { color:#B3AEC4; font-size:.75rem; margin-top:22px; }
    .floating-card { position:absolute; z-index:2; display:flex; align-items:center; gap:16px; width:clamp(270px,24vw,350px); min-height:104px; padding:22px 24px; color:#FFFFFF; background:linear-gradient(135deg,rgba(30,23,46,.88),rgba(19,16,29,.78)); border:1px solid rgba(205,178,255,.55); border-radius:22px; box-shadow:0 18px 55px rgba(0,0,0,.42),0 0 28px rgba(124,58,237,.16),inset 0 1px 0 rgba(255,255,255,.10); backdrop-filter:blur(20px); font-size:1rem; transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease; }
    .floating-card:hover { transform:translateY(-5px); border-color:rgba(224,202,255,.9); box-shadow:0 22px 60px rgba(0,0,0,.48),0 0 34px rgba(124,58,237,.25); }
    .floating-card b { display:block; color:#FFFFFF; font:800 clamp(1rem,1.15vw,1.18rem)/1.3 'Manrope',sans-serif; letter-spacing:-.025em; }
    .floating-card small { display:block; color:#D3C9E4; font-size:clamp(.8rem,.9vw,.92rem); line-height:1.45; margin-top:7px; }
    .floating-icon { display:grid; flex:0 0 52px; place-items:center; width:52px; height:52px; border-radius:16px; color:#E4D5FF; background:linear-gradient(145deg,rgba(142,91,255,.34),rgba(104,61,186,.16)); border:1px solid rgba(205,178,255,.28); font-size:1.55rem; box-shadow:inset 0 1px 0 rgba(255,255,255,.12); }
    .floating-left { left:clamp(24px,5vw,90px); top:39%; }
    .floating-right { right:clamp(24px,5vw,90px); top:38%; }
    .floating-bottom-left { left:clamp(24px,9vw,160px); bottom:8%; }
    .floating-bottom-right { right:clamp(24px,9vw,160px); bottom:8%; }
    /* Streamlit renders each st.markdown/st.button call as separate blocks,
       so position the keyed button block itself instead of a wrapper div. */
    .stApp:has(.landing-shell) .st-key-start_brieflyy {
      position:fixed !important; z-index:10010 !important; left:50% !important;
      top:calc(50% + 175px) !important; transform:translateX(-50%) !important;
      width:min(340px,calc(100vw - 40px)) !important; margin:0 !important;
      padding:0 !important;
    }
    .stApp:has(.landing-shell) .st-key-start_brieflyy button {
      width:100% !important; min-height:3.5rem !important; font-size:.96rem !important;
      font-weight:800 !important; color:#FFFFFF !important;
      border:1px solid rgba(225,205,255,.75) !important;
      background:linear-gradient(110deg,#7041D8,#9568FF) !important;
      box-shadow:0 0 30px rgba(126,70,240,.48), inset 0 1px 0 rgba(255,255,255,.18) !important;
    }
    .stApp:has(.landing-shell) .st-key-start_brieflyy button:hover {
      border-color:#FFFFFF !important; filter:brightness(1.12);
      box-shadow:0 0 38px rgba(153,105,255,.68) !important;
    }
    .landing-disclaimer { position:fixed; z-index:10001; left:20px; right:20px; bottom:22px; text-align:center; color:#A8A4B5; font-size:.75rem; margin:0; }
    @media(max-width:1100px) { .floating-card { width:260px; min-height:88px; padding:16px 18px; gap:12px; } .floating-icon { flex-basis:42px; width:42px; height:42px; font-size:1.3rem; } .floating-card b { font-size:.98rem; } .floating-card small { font-size:.78rem; } .floating-left { left:18px; } .floating-right { right:18px; } .floating-bottom-left { left:28px; bottom:5%; } .floating-bottom-right { right:28px; bottom:5%; } }
    @media(max-width:850px) { .landing-nav-links span:not(:last-child){display:none} .floating-card{display:none} .landing-content{padding:clamp(65px,12vh,110px) 22px 120px} .stApp:has(.landing-shell) .st-key-start_brieflyy{top:calc(50% + 180px)!important} }
    @media(max-width:560px) { .landing-nav{padding:16px 18px} .landing-content{padding:72px 20px 120px} .landing-title{font-size:2.45rem!important} .landing-proof{gap:9px 14px;font-size:.72rem} .stApp:has(.landing-shell) .st-key-start_brieflyy{top:auto!important;bottom:75px!important} .landing-disclaimer{bottom:15px;font-size:.66rem} }
    div[data-testid="stButton"] button[kind="primary"] { border-radius:12px; font-weight:800; min-height:3.2rem; }

    /* Unified Brieflyy theme: cinematic black + violet across BOTH pages */
    .stApp:not(:has(.landing-shell)) {
      background: radial-gradient(ellipse at 80% 0%, rgba(124,58,237,.16), transparent 34%),
                  radial-gradient(ellipse at 0% 80%, rgba(91,33,182,.10), transparent 30%),
                  linear-gradient(180deg,#0A0910 0%,#100D18 100%) !important;
      color:#F4F0FC !important;
    }
    .stApp:not(:has(.landing-shell)) .block-container { max-width:1440px; padding-top:1.4rem; }
    .stApp:not(:has(.landing-shell)) h1,
    .stApp:not(:has(.landing-shell)) h2,
    .stApp:not(:has(.landing-shell)) h3,
    .stApp:not(:has(.landing-shell)) h4,
    .stApp:not(:has(.landing-shell)) [data-testid="stMarkdownContainer"] p,
    .stApp:not(:has(.landing-shell)) label,
    .stApp:not(:has(.landing-shell)) .stCaption,
    .stApp:not(:has(.landing-shell)) [data-testid="stCaptionContainer"] { color:#E8E1F4 !important; }
    .stApp:not(:has(.landing-shell)) .brand-name { color:#FFFFFF !important; }
    .stApp:not(:has(.landing-shell)) .brand-sub,
    .stApp:not(:has(.landing-shell)) .section-desc { color:#B8ADC9 !important; }
    .stApp:not(:has(.landing-shell)) .hero {
      background:linear-gradient(115deg,rgba(28,18,43,.94),rgba(61,35,94,.90) 58%,rgba(85,49,139,.88)) !important;
      border:1px solid rgba(206,177,255,.20);
      box-shadow:0 18px 55px rgba(0,0,0,.24), inset 0 1px rgba(255,255,255,.05);
    }
    .stApp:not(:has(.landing-shell)) .hero h1 { color:#FFFFFF !important; }
    .stApp:not(:has(.landing-shell)) .hero p,
    .stApp:not(:has(.landing-shell)) .hero-note { color:#E3D8F4 !important; }
    .stApp:not(:has(.landing-shell)) .section-kicker { color:#C5A5FF !important; }
    .stApp:not(:has(.landing-shell)) .section-title { color:#FFFFFF !important; }
    .stApp:not(:has(.landing-shell)) .step-card,
    .stApp:not(:has(.landing-shell)) .soft-card,
    .stApp:not(:has(.landing-shell)) [data-testid="stVerticalBlockBorderWrapper"] {
      background:rgba(24,19,34,.82) !important;
      border-color:rgba(205,180,255,.17) !important;
      box-shadow:0 10px 30px rgba(0,0,0,.18) !important;
      color:#F4F0FC !important;
    }
    .stApp:not(:has(.landing-shell)) .step-title { color:#FFFFFF !important; }
    .stApp:not(:has(.landing-shell)) .step-copy { color:#BEB2D0 !important; }
    .stApp:not(:has(.landing-shell)) .step-number { color:#E8D8FF !important; background:rgba(139,92,246,.22) !important; }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] {
      background:linear-gradient(180deg,#100D18,#151020) !important;
      border-right:1px solid rgba(205,180,255,.14) !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] * { color:#E8E1F4; }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] {
      background:rgba(139,92,246,.08) !important; border-color:rgba(205,180,255,.38) !important;
    }
    .stApp:not(:has(.landing-shell)) input,
    .stApp:not(:has(.landing-shell)) textarea,
    .stApp:not(:has(.landing-shell)) [data-baseweb="select"] > div,
    .stApp:not(:has(.landing-shell)) [data-baseweb="input"] > div {
      background:#171321 !important; color:#FFFFFF !important;
      border-color:rgba(205,180,255,.25) !important;
    }
    .stApp:not(:has(.landing-shell)) input::placeholder,
    .stApp:not(:has(.landing-shell)) textarea::placeholder { color:#A99BBE !important; }
    .stApp:not(:has(.landing-shell)) .stButton > button[kind="primary"],
    .stApp:not(:has(.landing-shell)) .stDownloadButton > button {
      background:linear-gradient(110deg,#7C3AED,#A855F7) !important;
      color:#FFFFFF !important; border:1px solid rgba(224,199,255,.38) !important;
      box-shadow:0 6px 22px rgba(124,58,237,.28) !important;
    }
    .stApp:not(:has(.landing-shell)) .stButton > button:not([kind="primary"]),
    .stApp:not(:has(.landing-shell)) .stLinkButton > a {
      background:#21182E !important; color:#F2EAFE !important;
      border:1px solid rgba(205,180,255,.25) !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stMetric"] {
      background:rgba(139,92,246,.10) !important; border-color:rgba(205,180,255,.18) !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stMetricLabel"] { color:#C8BADB !important; }
    .stApp:not(:has(.landing-shell)) [data-testid="stMetricValue"] { color:#D9B8FF !important; }
    .stApp:not(:has(.landing-shell)) .badge,
    .stApp:not(:has(.landing-shell)) .job-label {
      background:rgba(139,92,246,.18) !important; color:#E6D5FF !important;
      border-color:rgba(205,180,255,.25) !important;
    }
    .stApp:not(:has(.landing-shell)) .stTabs [aria-selected="true"] { color:#D9B8FF !important; border-bottom-color:#A855F7 !important; }
    .stApp:not(:has(.landing-shell)) hr { border-color:rgba(205,180,255,.16) !important; }

    /* CV uploader: pale lavender surface + dark text for reliable contrast */
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] {
      background: #F7F3FF !important;
      border: 1px dashed #9B7ACB !important;
      border-radius: 16px !important;
      padding: 14px !important;
      color: #302044 !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] section,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
      background: #F7F3FF !important;
      border: 0 !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] *,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] p,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] span,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] small {
      color: #302044 !important;
      opacity: 1 !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
      background: #6D28D9 !important;
      color: #FFFFFF !important;
      border: 1px solid #6D28D9 !important;
      border-radius: 9px !important;
      font-weight: 800 !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] button * {
      color: #FFFFFF !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
      background: #5B21B6 !important;
      border-color: #5B21B6 !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] h1,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] h2,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] h3,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] h4,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] label,
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] p {
      color:#F3ECFC !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
      color:#C9B9DD !important;
    }
    .stApp:not(:has(.landing-shell)) [data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {
      border-color:#E9D8FF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Two-page experience ──────────────────────────────────────────────────────
if "brieflyy_page" not in st.session_state:
    st.session_state["brieflyy_page"] = "landing"

if st.session_state["brieflyy_page"] == "landing":
    # Replace this URL through Streamlit secrets with your preferred direct MP4 URL.
    try:
        hero_video = st.secrets.get("HERO_VIDEO_URL", "https://videos.pexels.com/video-files/3130284/3130284-hd_1920_1080_30fps.mp4")
    except Exception:
        hero_video = "https://videos.pexels.com/video-files/3130284/3130284-hd_1920_1080_30fps.mp4"
    st.markdown(
        f"""<div class="landing-shell">
          <video class="landing-video" autoplay muted loop playsinline preload="metadata" aria-hidden="true">
            <source src="{hero_video}" type="video/mp4">
          </video>
          <div class="landing-overlay"></div>
          <div class="landing-nav">
            <div class="landing-brand"><div class="landing-mark">B.</div>
              <div><div class="landing-brand-name">Brieflyy</div><div class="landing-brand-sub">AI Career Copilot</div></div>
            </div>
            <div class="landing-nav-links"><span>Features</span><span>How it works</span><span>AI-powered matching</span><span>Get started →</span></div>
          </div>
          <div class="landing-content">
            <div class="landing-eyebrow">Your next chapter starts here</div>
            <div class="landing-title">Your AI Copilot for<br><span>Career Growth</span></div>
            <div class="landing-copy">Find opportunities that fit your skills, understand your CV match, and prepare stronger applications — with AI that keeps your experience authentic.</div>
            <div class="landing-proof"><span>✓ CV insights</span><span>✓ Smarter job matching</span><span>✓ ATS analysis</span></div>
            <div class="landing-foot">One CV. Better-matched opportunities. More confident applications.</div>
          </div>
          <div class="floating-card floating-left"><div class="floating-icon">▤</div><div><b>Resume insights</b><small>Skills and experience analysed</small></div></div>
          <div class="floating-card floating-right"><div class="floating-icon">↗</div><div><b>CV match score</b><small>Understand your fit for each role</small></div></div>
          <div class="floating-card floating-bottom-left"><div class="floating-icon">✓</div><div><b>Authentic adaptation</b><small>Your experience stays yours</small></div></div>
          <div class="floating-card floating-bottom-right"><div class="floating-icon">◎</div><div><b>Interview-ready</b><small>Take the next step with confidence</small></div></div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="landing-cta">', unsafe_allow_html=True)
    if st.button("Find matching jobs · Upload my CV  →", type="primary", use_container_width=True, key="start_brieflyy"):
        st.session_state["brieflyy_page"] = "workspace"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-disclaimer">Your CV stays under your control. Nothing is sent to an employer without your action.</div>', unsafe_allow_html=True)
    st.stop()

# ── Header ───────────────────────────────────────────────────────────────────
_, home_col = st.columns([6, 1], vertical_alignment="center")
with home_col:
    if st.button("← Home", use_container_width=True, key="back_home"):
        st.session_state["brieflyy_page"] = "landing"
        st.rerun()
st.markdown(
    """
    <div class="brand-row">
      <div class="brand-mark">B.</div>
      <div>
        <div class="brand-name">Brieflyy</div>
        <div class="brand-sub">Your AI career copilot</div>
      </div>
    </div>
    <div class="hero">
      <span class="hero-eyebrow">Your career workspace</span>
      <h1>Find the right role.<br>Show them your best.</h1>
      <p>Discover relevant opportunities, understand how well your CV fits, and create a tailored version that stays true to your experience.</p>
      <div class="hero-note">✓ Your experience stays yours &nbsp;&nbsp; · &nbsp;&nbsp; ✓ You stay in control of every application</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-kicker">Career workspace</div>'
    '<div class="section-title">Let’s find your next move</div>'
    '<div class="section-desc">Upload your CV, choose what you’re looking for, and explore opportunities matched to your profile.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div style="padding:4px 0 16px">
          <div style="font-size:.72rem;font-weight:800;letter-spacing:.12em;color:#C7A8F7;text-transform:uppercase">YOUR WORKSPACE</div>
          <div style="font:800 1.3rem 'Manrope',sans-serif;color:#FFFFFF;margin-top:5px">Build your next step</div>
          <div style="font-size:.86rem;color:#D4C9E4;margin-top:7px;line-height:1.55">A few details help us find more relevant roles.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("#### 01 · Your CV")
    uploaded = st.file_uploader("Upload your CV", type=["pdf"], help="PDF format")
    if uploaded:
        st.success("CV added to this session")
    st.divider()
    st.markdown("#### 02 · Your search")
    search = st.text_input("Role, skill or keyword", value="python", placeholder="e.g. Data Analyst")
    limit = st.slider("Offers per source", 1, 10, 3)
    st.divider()

# Demo mode is disabled by default and its control is hidden from the interface.
demo_mode = False

# How it works
st.markdown("### A simpler way to job hunt")
st.markdown('<div class="section-desc">From your current CV to a more targeted application, in three steps.</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    st.markdown('<div class="step-card"><div class="step-number">01</div><div class="step-title">Add your CV</div><div class="step-copy">We read your PDF to understand your experience, projects and skills.</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="step-card"><div class="step-number">02</div><div class="step-title">Explore opportunities</div><div class="step-copy">Search current offers and open the original listing whenever you’re ready.</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="step-card"><div class="step-number">03</div><div class="step-title">Tailor with confidence</div><div class="step-copy">Review match and ATS scores, check changes, then download your adapted CV.</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Prototype · Job listings from Remotive and Adzuna. AI-generated suggestions should always be reviewed before use.")

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


def cv_view(cv: dict) -> str:
    lines = [f"**{cv.get('titre') or ''}**", "", "**Skills:** " + ", ".join(cv.get("competences", [])), ""]
    for exp in cv.get("experiences", []):
        tag = " *(most relevant)*" if exp.get("pertinente") else ""
        lines.append(f"**{exp.get('poste', '')}** at {exp.get('entreprise', '')} ({exp.get('dates', '')}){tag}")
        lines += [f"- {m}" for m in exp.get("missions", [])]
        lines.append("")
    return "\n".join(lines)


def fidelity_sentence(report: dict) -> str:
    return (
        f"{report.get('reformulees', 0)} mission(s) reworded, "
        f"{report.get('conservees', 0)} kept word for word. "
        "No skill, employer, date or figure was added."
    )


def show_result(profile: dict, offer: dict, result: dict):
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📄 Adapted CV", "✓ Fidelity check"])

    with tab1:
        st.markdown("#### Your application snapshot")
        c1, c2, c3, c4 = st.columns(4, gap="small")
        c1.metric("CV match", pct(result["match_original"]))
        c2.metric("Adapted match", pct(result["match_adapted"]))
        c3.metric("Original ATS", pct(result["ats_original"]["score"]))
        c4.metric("Adapted ATS", pct(result["ats_adapted"]["score"]))
        missing = result["ats_adapted"]["missing"]
        if missing:
            st.markdown("**Keywords to consider**")
            st.markdown(" ".join(f"<span class='badge'>{m}</span>" for m in missing), unsafe_allow_html=True)
        else:
            st.success("Your adapted CV covers all the offer keywords detected by the checker.")
        gaps = result.get("gaps") or []
        if gaps:
            st.markdown("**Potential gaps to review**")
            for g in gaps:
                st.markdown(f"- {g}")

    with tab2:
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("#### Original profile")
            with st.container(border=True):
                st.markdown(cv_view(profile))
        with right:
            st.markdown("#### Tailored version")
            with st.container(border=True):
                st.markdown(cv_view(result["cv"]))
        pdf_bytes = render_cv_pdf(result["cv"], title=offer["title"])
        st.download_button(
            "⬇  Download adapted CV (PDF)",
            pdf_bytes,
            file_name="CV_adapted.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        with st.expander("Preview the adapted PDF"):
            b64 = base64.b64encode(pdf_bytes).decode("ascii")
            components.html(
                f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700" style="border:1px solid #E7EAF2;border-radius:12px;background:white"></iframe>',
                height=720,
            )

    with tab3:
        st.markdown("#### A transparent adaptation")
        st.info(fidelity_sentence(result.get("report", {})))
        st.caption("Review the wording before applying. Adaptation should clarify your experience, never invent it.")
        original_missions = [m for e in profile.get("experiences", []) for m in e.get("missions", [])]
        adapted_missions = [m for e in result["cv"].get("experiences", []) for m in e.get("missions", [])]
        if original_missions:
            st.markdown("**Original vs. adapted missions**")
            for orig, new in zip(original_missions, adapted_missions):
                with st.container(border=True):
                    if orig == new:
                        st.markdown(f"**Unchanged** · {orig}")
                    else:
                        st.markdown(f"**Original**  \n{orig}  \n\n**Adapted**  \n{new}")

if not uploaded:
    st.markdown(
        """
        <div class="soft-card" style="margin-top:20px">
          <div style="font:800 1.05rem 'Manrope',sans-serif;color:#202A43">Ready when you are</div>
          <div style="color:#7A8499;font-size:.9rem;margin-top:6px;line-height:1.6">
            Upload your CV in the left panel to unlock personalised job matching and CV analysis.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

try:
    with st.spinner("Reading your CV..."):
        profile = profile_from_pdf(uploaded.getvalue())
except Exception as e:
    st.error(f"Could not read your CV: {e}")
    st.stop()

st.success(f"CV loaded: {profile.get('nom') or 'your profile'}")
st.markdown("---")
search_col, button_col = st.columns([4, 1], vertical_alignment="bottom")
with search_col:
    st.markdown("### Opportunities for you")
    st.caption(f"Searching for **{search}** across supported job sources.")
with button_col:
    search_clicked = st.button("⌕  Search offers", type="primary", use_container_width=True)

if search_clicked:
    try:
        with st.spinner("Finding relevant opportunities..."):
            st.session_state["offers"] = (
                fetch_remotive_jobs(search, limit) + fetch_adzuna_jobs(search, limit)
            )
    except Exception as e:
        st.error(f"Could not load offers: {e}")

offers = st.session_state.get("offers", [])
if not offers:
    st.info("Your results will appear here. Select **Search offers** to discover available roles.")
    st.stop()

st.markdown(f"**{len(offers)} opportunities found**")
st.caption("Open the original listing to apply, or analyse how your CV aligns with the role.")

for i, offer in enumerate(offers):
    with st.container(border=True):
        top_left, top_right = st.columns([4, 1], vertical_alignment="center")
        with top_left:
            st.markdown(f"### {offer['title']}")
            st.markdown(
                f'<div class="job-subtitle">🏢 &nbsp; {offer["company"]} &nbsp;&nbsp; · &nbsp;&nbsp; 📍 &nbsp; {offer["location"]}</div>',
                unsafe_allow_html=True,
            )
        with top_right:
            st.markdown(
                f'<div style="text-align:right"><span class="job-label">{offer["source"]}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        b1, b2 = st.columns([1, 1], gap="small")
        with b1:
            analyse = st.button("Analyse my CV", key=f"btn_{i}", type="primary", use_container_width=True)
        with b2:
            st.link_button("↗  View original offer", offer["url"], use_container_width=True)

        if analyse:
            with st.spinner("Analysing the role and tailoring your CV..."):
                try:
                    st.session_state[f"res_{i}"] = get_result(profile, offer)
                except Exception as e:
                    st.error(str(e))

        result = st.session_state.get(f"res_{i}")
        if result is None and demo_mode:
            st.warning("No saved result for this offer yet. Turn off Demo mode to generate an analysis.")
        elif result:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            show_result(profile, offer, result)
