import html
import streamlit as st
from services.gas_client import get_data
from views import admin, guru, siswa, penugasan



st.set_page_config(
    page_title="Dashboard SMPN 1 Dawuan",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)


ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin")



st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap');

:root {
    --navy: #0B2559;
    --navy-deep: #06173D;
    --blue: #1F63DB;
    --blue-dark: #174CB0;
    --sky: #5AAEFF;
    --soft: #E8F1FF;
    --mist: #F3F7FE;
    --text: #13294D;
    --muted: #5A6F94;
    --line: #D3E0F4;
}

/* ---------- Dasar ---------- */
html, body, .stApp, button, input, textarea, [class*="css"] {
    font-family: 'Manrope', 'Segoe UI', sans-serif;
}
h1, h2, h3, .brand-name, .login-title, .side-title, .page-heading h1, .identity-name {
    font-family: 'Sora', 'Manrope', sans-serif;
}
#MainMenu, footer, [data-testid="stSidebar"] { visibility: hidden; display: none; }
[data-testid="stAppViewContainer"], .stApp {
    background-color: #EAF1FC;
    background-image:
        linear-gradient(rgba(31,99,219,.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(31,99,219,.045) 1px, transparent 1px),
        linear-gradient(180deg, #F2F7FF 0%, #E3EDFB 100%);
    background-size: 36px 36px, 36px 36px, 100% 100%;
    color: var(--text);
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1240px; padding-top: 1.1rem; padding-bottom: 3rem; }

/* ---------- Header ---------- */
.topbar {
    display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 1rem;
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-bottom: 4px solid var(--blue);
    border-radius: 20px 20px 14px 14px;
    padding: .8rem 1.2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 12px 28px rgba(11, 37, 89, .10);
}
.brand-wrap { display: flex; align-items: center; justify-content: center; text-align: center; }
.topbar .user-chip { justify-self: end; }
.brand-kicker { color: var(--muted) !important; font-size: .8rem; font-weight: 600; line-height: 1.2; }
.brand-name { color: var(--navy) !important; font-size: 1.15rem; font-weight: 800; line-height: 1.25; }
.user-chip {
    display: flex; align-items: center; gap: .65rem;
    background: var(--soft); border: 1px solid #C4D9F6;
    border-radius: 999px; padding: .3rem 1.1rem .3rem .3rem;
}
.user-avatar {
    width: 38px; height: 38px; display: grid; place-items: center;
    border-radius: 50%; background: var(--blue); font-size: 1.1rem;
}
.user-name { color: var(--navy) !important; font-weight: 800; font-size: .86rem; line-height: 1.2; }
.user-role { color: var(--blue-dark) !important; font-size: .72rem; font-weight: 700; }

/* Halaman login */
.login-page { display: none; }
.block-container:has(.login-page),
[data-testid="stMainBlockContainer"]:has(.login-page) {
    padding-top: max(1rem, calc((100vh - 760px) / 2)) !important;
    padding-bottom: 1rem !important;
}

/* ---------- Halaman login ---------- */
.st-key-login_shell,
[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-login_shell) {
    background:
        radial-gradient(circle at 85% 8%, rgba(90,174,255,.55) 0%, rgba(90,174,255,0) 46%),
        linear-gradient(160deg, #1247B0 0%, #0B2559 60%, #06173D 100%) !important;
    border: 1px solid rgba(255,255,255,.18) !important;
    border-radius: 28px !important;
    box-shadow: 0 24px 54px rgba(11, 37, 89, .30) !important;
    overflow: hidden;
}
.st-key-login_shell { padding: 2.4rem 2.2rem !important; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-login_shell) { padding: 0 !important; }
.st-key-login_shell [data-testid="stVerticalBlock"],
.st-key-login_shell [data-testid="stColumn"],
.st-key-login_shell [data-testid="stForm"] { background: transparent !important; }


.st-key-login_shell .login-title { color: #FFFFFF !important; }
.st-key-login_shell .login-subtitle { color: #CFE2FF !important; }
.st-key-login_shell label,
.st-key-login_shell label p,
.st-key-login_shell [data-testid="stWidgetLabel"],
.st-key-login_shell [data-testid="stWidgetLabel"] * { color: #FFFFFF !important; font-weight: 700; }
.st-key-login_shell .login-title-icon {
    background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.45);
    color: #FFFFFF !important;
}
.st-key-login_shell .login-panel { border-bottom: 1px dashed rgba(255,255,255,.4); }
.st-key-login_shell [data-testid="stFormSubmitButton"] button[kind="primary"] {
    background: #FFFFFF !important; border-color: #FFFFFF !important;
    color: #0B2559 !important; box-shadow: 0 10px 22px rgba(3, 17, 48, .35);
}
.st-key-login_shell [data-testid="stFormSubmitButton"] button[kind="primary"] * { color: #0B2559 !important; }
.st-key-login_shell [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
    background: #E8F1FF !important;
}

.login-side { color: #FFFFFF; }
.side-badge {
    display: inline-block; padding: .3rem .85rem; border-radius: 999px;
    background: rgba(255,255,255,.16); color: #DCEBFF !important;
    font-size: .78rem; font-weight: 700; margin-bottom: 1.2rem;
}
.side-art { font-size: 4.2rem; line-height: 1; margin-bottom: 1rem; filter: drop-shadow(0 8px 10px rgba(0,0,0,.3)); }
.side-title { color: #FFFFFF !important; font-size: 1.85rem; font-weight: 800; line-height: 1.2; margin-bottom: .6rem; }
.side-text { color: #C9DFFF !important; font-size: .98rem; line-height: 1.55; margin-bottom: 1.4rem; }
.side-list { list-style: none; padding: 0; margin: 0; }
.side-list li {
    color: #FFFFFF !important; font-size: .92rem; font-weight: 600;
    padding: .5rem .8rem; margin-bottom: .5rem; border-radius: 12px;
    background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.14);
}
.side-list li::before { content: "✓"; color: #7FC0FF; font-weight: 800; margin-right: .6rem; }

.login-panel { padding-bottom: .9rem; margin-bottom: 1.1rem; border-bottom: 1px dashed #C7D8F2; }
.login-title-row { display: block; }
.login-title-icon {
    width: 56px; height: 56px; display: grid; place-items: center; margin-bottom: .9rem;
    border-radius: 16px; background: var(--soft); color: var(--blue) !important;
    font-size: 1.9rem; border: 1px solid #C4D9F6;
}
.login-title { color: var(--navy) !important; font-size: 1.75rem; font-weight: 800; line-height: 1.2; }
.login-subtitle { color: var(--muted) !important; font-size: .95rem; margin-top: .35rem; }

[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

.section-title { color: var(--navy) !important; font-size: 1.4rem; font-weight: 800; }
.section-subtitle { color: var(--muted) !important; font-size: .95rem; margin: 0 0 1rem; }
.role-card-head { display: flex; align-items: center; gap: 1rem; padding: .3rem .1rem .7rem; }
.role-icon { width: 70px; text-align: center; font-size: 2.8rem; color: var(--blue); }
.role-kicker { color: var(--muted) !important; font-size: .9rem; font-weight: 600; }
.role-name { color: var(--navy) !important; font-size: 1.3rem; font-weight: 800; }

/* ---------- Judul halaman ---------- */
.page-heading {
    display: flex; align-items: center; gap: 1rem;
    background: #FFFFFF; border: 1px solid var(--line);
    border-left: 8px solid var(--blue);
    border-radius: 16px; padding: .95rem 1.3rem; margin: .4rem 0 1.3rem;
    box-shadow: 0 6px 16px rgba(11, 37, 89, .06);
}
.page-heading-icon {
    width: 44px; height: 44px; flex: 0 0 44px; display: grid; place-items: center;
    border-radius: 50%; background: var(--soft); color: var(--blue) !important;
    font-size: 1.35rem; font-weight: 800; border: 1px solid #C4D9F6;
}
.page-heading h1 { color: var(--navy) !important; font-size: 1.45rem; font-weight: 800; margin: 0; line-height: 1.2; }
.page-heading p { color: var(--muted) !important; margin: .15rem 0 0; font-size: .88rem; }
.page-heading p:empty { display: none; }

/* ---------- Panel umum dan identitas ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    box-shadow: 0 6px 18px rgba(11, 37, 89, .07);
}
.identity-layout { display: flex; align-items: center; gap: 1.2rem; padding: .5rem .2rem 1rem; }
.identity-avatar {
    width: 104px; height: 104px; flex: 0 0 104px; border-radius: 28px;
    display: grid; place-items: center; background: var(--soft);
    color: var(--blue) !important; font-size: 3.6rem; border: 2px solid #BBD5FA;
}
.identity-name { color: var(--navy) !important; font-size: 1.3rem; font-weight: 800; margin-bottom: .4rem; }
.identity-detail { color: #2A4571 !important; font-size: .95rem; margin: .25rem 0; }



[data-testid="stVerticalBlockBorderWrapper"]:not(:has(.login-side)) > div,
[data-testid="stVerticalBlockBorderWrapper"]:not(:has(.login-side)) [data-testid="stVerticalBlock"] {
    background-color: #FFFFFF !important;
}



[class*="st-key-card_"],
[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-card_"]) {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 20px rgba(11, 37, 89, .08) !important;
}
[class*="st-key-card_"] {
    padding: 1.1rem 1.3rem 1.2rem !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-card_"]) [class*="st-key-card_"] {
    border: none !important; box-shadow: none !important; padding: .4rem .5rem !important;
}

/* ---------- Teks global ---------- */
[data-testid="stAppViewContainer"] .stMarkdown,
[data-testid="stAppViewContainer"] .stMarkdown p,
[data-testid="stAppViewContainer"] .stMarkdown li,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] label { color: var(--navy); }
[data-testid="stAppViewContainer"] h3 {
    font-weight: 800; font-size: 1.2rem;
    padding-left: .75rem; border-left: 5px solid var(--sky); line-height: 1.25;
}
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] { color: var(--muted) !important; }


.login-side, .login-side * { -webkit-text-fill-color: initial; }
[data-testid="stAppViewContainer"] .login-side .side-title,
[data-testid="stAppViewContainer"] .login-side .side-list li { color: #FFFFFF !important; }
[data-testid="stAppViewContainer"] .login-side .side-text { color: #C9DFFF !important; }
[data-testid="stAppViewContainer"] .login-side .side-badge { color: #DCEBFF !important; }


[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background-color: #FFFFFF !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    border: none !important; box-shadow: none !important; outline: none !important;
    caret-color: var(--blue) !important;
    font-weight: 600;
}
[data-testid="stTextInput"] input:-webkit-autofill,
[data-testid="stTextInput"] input:-webkit-autofill:hover,
[data-testid="stTextInput"] input:-webkit-autofill:focus {
    -webkit-text-fill-color: var(--text) !important;
    -webkit-box-shadow: 0 0 0 1000px #FFFFFF inset !important;
    box-shadow: 0 0 0 1000px #FFFFFF inset !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #7389AD !important; -webkit-text-fill-color: #7389AD !important; opacity: 1 !important;
}
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextInput"] [data-baseweb="base-input"],
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stNumberInput"] [data-baseweb="input"] {
    background-color: #FFFFFF !important;
    border: 2px solid #B9CCE8 !important;
    border-radius: 14px !important;
}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
[data-testid="stTextInput"] [data-baseweb="base-input"]:focus-within,
[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within,
[data-testid="stNumberInput"] [data-baseweb="input"]:focus-within {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 4px rgba(31, 99, 219, .16) !important;
}

/* ---------- Dropdown ---------- */
[data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
[data-testid="stSelectbox"] div[role="combobox"],
.stSelectbox div[data-baseweb="select"] > div,
.stSelectbox div[role="combobox"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    background-image: none !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    border-color: #B9CCE8 !important;
    border-radius: 14px !important;
    box-shadow: none !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] *,
[data-testid="stSelectbox"] div[role="combobox"] *,
.stSelectbox div[data-baseweb="select"] *,
[data-testid="stSelectbox"] input {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    font-weight: 600;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
[data-testid="stSelectbox"] div[role="combobox"]:focus,
[data-testid="stSelectbox"] div[role="combobox"]:focus-within {
    background: #FFFFFF !important;
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 3px rgba(31, 99, 219, .18) !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] svg { color: var(--blue) !important; fill: var(--blue) !important; }
[data-baseweb="popover"], [data-baseweb="menu"] { background-color: #FFFFFF !important; border-radius: 14px !important; }
[role="option"] { background-color: #FFFFFF !important; color: var(--text) !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background-color: var(--soft) !important; }


div.stButton > button,
div.stDownloadButton > button,
[data-testid="stFormSubmitButton"] button {
    min-height: 2.8rem;
    border-radius: 999px;
    font-weight: 800;
    letter-spacing: .01em;
    border: 2px solid var(--blue) !important;
    color: var(--blue-dark) !important;
    background: #FFFFFF !important;
    transition: all .15s ease;
}
div.stButton > button:hover,
div.stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    background: var(--soft) !important;
    color: var(--navy) !important;
    border-color: var(--navy) !important;
}
div.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #3C86F0 0%, #1F63DB 50%, #0F3FA0 100%) !important;
    border-color: transparent !important;
    box-shadow: 0 10px 20px rgba(31, 99, 219, .35);
}
div.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1F63DB 0%, #0B2559 100%) !important;
    transform: translateY(-1px);
}
div.stButton > button[kind="primary"] *,
[data-testid="stFormSubmitButton"] button[kind="primary"] * { color: #FFFFFF !important; }
div.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"] { color: #FFFFFF !important; }

/* ---------- Navigasi admin ---------- */
[data-testid="stRadio"] [role="radiogroup"] {
    display: flex; flex-wrap: wrap; gap: .3rem;
    background: var(--navy); border-radius: 999px; padding: .35rem;
    box-shadow: 0 10px 22px rgba(11, 37, 89, .22);
}
[data-testid="stRadio"] [role="radiogroup"] label {
    flex: 1 1 0; justify-content: center; margin: 0;
    padding: .5rem 1rem; border-radius: 999px; cursor: pointer;
}
[data-testid="stRadio"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stRadio"] [role="radiogroup"] label p {
    color: #B9D3FA !important; font-weight: 700; text-align: center; font-size: .9rem;
}
[data-testid="stRadio"] [role="radiogroup"] label:hover { background: rgba(255,255,255,.10); }
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
    background: #FFFFFF;
}
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p {
    color: var(--navy) !important; font-weight: 800;
}
[data-testid="stTabs"] button { color: var(--navy) !important; }

/* ---------- Notifikasi ---------- */
[data-testid="stAlert"] {
    background-color: var(--soft) !important;
    border: 1px solid #B5D0F7 !important;
    border-left: 6px solid var(--blue) !important;
    border-radius: 14px !important;
}
[data-testid="stAlert"] > div { background-color: var(--soft) !important; }
[data-testid="stAlert"] p, [data-testid="stAlert"] span, [data-testid="stAlert"] svg {
    color: var(--navy) !important; fill: var(--blue) !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]),
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) > div {
    background-color: #FDE8E8 !important; border-color: #F5B5B5 !important; border-left-color: #D32F2F !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) p,
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) span,
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) svg {
    color: #A61B1B !important; fill: #A61B1B !important;
}

/* ---------- Metric ---------- */
[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid var(--line);
    border-top: 5px solid var(--blue);
    padding: 14px 18px 16px; border-radius: 16px;
    box-shadow: 0 8px 18px rgba(11, 37, 89, .07);
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
    color: var(--muted) !important; font-weight: 700; font-size: .85rem;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] *,
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {
    color: var(--navy) !important; font-weight: 800; font-family: 'Sora', sans-serif;
}

/* ---------- Tabel, expander, pemisah ---------- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    background: #FFFFFF; border: 1px solid var(--line);
    border-radius: 16px; overflow: hidden;
    box-shadow: 0 8px 18px rgba(11, 37, 89, .07);
}
[data-testid="stExpander"] {
    background: #FFFFFF; border: 1px solid var(--line) !important; border-radius: 16px !important;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {
    color: var(--navy) !important; font-weight: 800;
}
hr { border: none !important; height: 2px; background: linear-gradient(90deg, #B9CCE8, rgba(185,204,232,0)); }

/* ---------- Layar kecil ---------- */
@media (max-width: 700px) {
    .topbar { padding: .6rem .7rem; grid-template-columns: 1fr; justify-items: center; }
    .topbar > div:empty { display: none; }
    .topbar .user-chip { justify-self: center; }
    .brand-name { font-size: .98rem; }
    .user-chip { padding-right: .7rem; }
    .side-title { font-size: 1.4rem; }
    .page-heading { padding: .75rem .9rem; }
    .identity-layout { align-items: flex-start; }
    .identity-avatar { width: 72px; height: 72px; flex-basis: 72px; font-size: 2.6rem; }
    [data-testid="stRadio"] [role="radiogroup"] { border-radius: 22px; }
}


[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] div,
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSelectbox"] [data-baseweb="select"] input,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within div,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within input {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    background-image: none !important;
    color: #13294D !important;
    -webkit-text-fill-color: #13294D !important;
    caret-color: #1F63DB !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    border: 2px solid #B9CCE8 !important;
    border-radius: 14px !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
    border-color: #1F63DB !important;
    box-shadow: 0 0 0 3px rgba(31, 99, 219, .18) !important;
}
[data-baseweb="popover"] *,
[data-baseweb="menu"],
[data-baseweb="menu"] ul,
[data-baseweb="menu"] li {
    background-color: #FFFFFF;
    color: #13294D !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] li[aria-selected="true"] {
    background-color: #E8F1FF !important;
}


.page-heading { padding: .7rem 1.1rem !important; gap: .8rem !important; }
.page-heading h1 { font-size: 1.2rem !important; }
.page-heading-icon { width: 38px !important; height: 38px !important; flex-basis: 38px !important; font-size: 1.1rem !important; }
[data-testid="stAppViewContainer"] h3 { font-size: 1.05rem !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { font-size: .8rem !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { font-size: 1.6rem !important; }
div.stButton > button, div.stDownloadButton > button,
[data-testid="stFormSubmitButton"] button { min-height: 2.4rem !important; }
div.stButton > button *, div.stDownloadButton > button *,
[data-testid="stFormSubmitButton"] button * { font-size: .85rem !important; }


div.stDownloadButton, [data-testid="stDownloadButton"] {
    display: flex !important; justify-content: flex-start !important; width: 100% !important;
}
div.stDownloadButton > button, [data-testid="stDownloadButton"] > button {
    width: auto !important; min-width: 0 !important; max-width: 340px !important;
    padding-left: 1.6rem !important; padding-right: 1.6rem !important;
}


html, :root { font-size: 14px !important; }
.block-container { max-width: 1100px !important; padding-top: .8rem !important; }

.topbar { padding: .45rem 1rem !important; margin-bottom: 1rem !important; border-bottom-width: 3px !important; }
.brand-kicker { font-size: .68rem !important; }
.brand-name { font-size: 1rem !important; }
.user-chip { padding: .2rem .8rem .2rem .2rem !important; gap: .5rem !important; }
.user-avatar { width: 30px !important; height: 30px !important; font-size: .9rem !important; }
.user-name { font-size: .75rem !important; }
.user-role { font-size: .65rem !important; }

.page-heading { padding: .5rem .9rem !important; gap: .65rem !important; margin: .2rem 0 .9rem !important; border-left-width: 6px !important; border-radius: 12px !important; }
.page-heading h1 { font-size: 1.05rem !important; }
.page-heading p { font-size: .75rem !important; }
.page-heading-icon { width: 30px !important; height: 30px !important; flex-basis: 30px !important; font-size: .95rem !important; }

[data-testid="stMetric"] { padding: 10px 14px 12px !important; border-top-width: 4px !important; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { font-size: .75rem !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { font-size: 1.3rem !important; }

div.stButton > button, div.stDownloadButton > button,
[data-testid="stFormSubmitButton"] button { min-height: 2.1rem !important; }
div.stButton > button *, div.stDownloadButton > button *,
[data-testid="stFormSubmitButton"] button * { font-size: .78rem !important; }
div.stDownloadButton > button, [data-testid="stDownloadButton"] > button { max-width: 280px !important; }

[data-testid="stAppViewContainer"] h3 { font-size: .95rem !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { font-size: .74rem !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { font-size: .85rem !important; }
[data-testid="stRadio"] [role="radiogroup"] label { padding: .35rem .8rem !important; }
[data-testid="stRadio"] [role="radiogroup"] label p { font-size: .8rem !important; }
[data-testid="stAlert"] p { font-size: .8rem !important; }
hr { margin: .7rem 0 !important; }
</style>
""", unsafe_allow_html=True)



if "data" not in st.session_state:
    try:
        st.session_state.data = get_data()
    except Exception as e:
        st.error(f"Tidak bisa terhubung ke Google Sheets: {e}")
        st.stop()

if "screen" not in st.session_state:
    st.session_state.screen = "login"

if st.session_state.screen not in ["login", "dashboard"]:
    st.session_state.screen = "login"

if "role" not in st.session_state:
    st.session_state.role = None

if "user" not in st.session_state:
    st.session_state.user = None




# HEADER
def header(user=None, role=None):
    
    user_html = ""
    if user:
        safe_name = html.escape(str(user.get("nama", "Pengguna")))
        safe_role = html.escape(str(role or ""))
        user_html = (
            '<div class="user-chip">'
            '<div class="user-avatar">👤</div>'
            '<div>'
            f'<div class="user-name">{safe_name}</div>'
            f'<div class="user-role">{safe_role}</div>'
            '</div>'
            '</div>'
        )

    st.markdown(
        '<div class="topbar">'
        '<div></div>'
        '<div class="brand-wrap">'
        '<div>'
        '<div class="brand-kicker">Sistem Informasi Sekolah</div>'
        '<div class="brand-name">SMPN 1 Dawuan</div>'
        '</div>'
        '</div>'
        f'{user_html or "<div></div>"}'
        '</div>',
        unsafe_allow_html=True
    )


def dashboard_header(user, role):
    header(user, role)


def page_heading(title, subtitle, icon="▦"):
    st.markdown(
        '<div class="page-heading">'
        f'<div class="page-heading-icon">{icon}</div>'
        '<div>'
        f'<h1>{html.escape(str(title))}</h1>'
        f'<p>{html.escape(str(subtitle))}</p>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


# LOGIN GURU DAN SISWA
def _login_siswa_guru():
    st.markdown(
        '<div class="login-subtitle" style="margin-bottom:.8rem;">'
        'Masukkan NISN untuk siswa atau NIP untuk guru.</div>',
        unsafe_allow_html=True
    )

    with st.form("login_form"):
        identifier = st.text_input(
            "NISN / NIP",
            placeholder="Masukkan NISN atau NIP",
            key="login_identifier",
            max_chars=20
        )
        submitted = st.form_submit_button(
            "Masuk ke Dashboard →",
            type="primary",
            use_container_width=True
        )

    if not submitted:
        return

    normalized = identifier.strip()

    if not normalized:
        st.error("NISN atau NIP wajib diisi.")
        return

    if not normalized.isdigit():
        st.error("NISN atau NIP harus berupa angka.")
        return

    guru_matches = [
        item for item in st.session_state.data["guru"]
        if str(item.get("nip", "")).strip() == normalized
        and str(item.get("nama", "")).strip()
        and str(item.get("kode", "")).strip()
    ]

    siswa_matches = [
        item for item in st.session_state.data["siswa"]
        if str(item.get("nisn", "")).strip() == normalized
        and str(item.get("nama", "")).strip()
        and str(item.get("kelas", "")).strip()
    ]

    if len(guru_matches) == 1 and len(siswa_matches) == 0:
        user, role = guru_matches[0], "Guru"
    elif len(siswa_matches) == 1 and len(guru_matches) == 0:
        user, role = siswa_matches[0], "Siswa"
    else:
        st.error(
            "NISN atau NIP tidak ditemukan, datanya tidak lengkap, "
            "atau nomor terdaftar lebih dari satu."
        )
        return

    _masuk(user, role)


def _login_admin():
    st.markdown(
        '<div class="login-subtitle" style="margin-bottom:.8rem;">'
        'Masukkan password untuk masuk sebagai administrator.</div>',
        unsafe_allow_html=True
    )

    with st.form("admin_login_form"):
        admin_password = st.text_input(
            "Password Admin",
            type="password",
            placeholder="Masukkan password admin"
        )
        submitted = st.form_submit_button(
            "Masuk sebagai Admin →",
            type="primary",
            use_container_width=True
        )

    if not submitted:
        return

    if admin_password == ADMIN_PASSWORD:
        _masuk({"nama": "Administrator"}, "Admin")
    else:
        st.error("Password Admin salah.")


def _masuk(user, role):
    st.session_state.user = user
    st.session_state.role = role
    st.session_state.screen = "dashboard"
    st.session_state.pop("guru_nav", None)
    st.session_state.pop("admin_nav", None)
    st.rerun()


def login_screen():
    st.markdown('<div class="login-page"></div>', unsafe_allow_html=True)
    header()

    with st.container(border=True, key="login_shell"):
        side_col, form_col = st.columns([1, 1.05], gap="large")

        with side_col:
            st.markdown(
                '<div class="login-side">'
                '<div class="side-badge">SMPN 1 Dawuan</div>'
                '<div class="side-art">🏫</div>'
                '<div class="side-title">Dashboard SMPN 1 Dawuan</div>'
                '<div class="side-text">'
                'Sistem informasi jadwal pelajaran dan rekap absensi.'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

        with form_col:
            st.markdown(
                '<div class="login-panel">'
                '<div class="login-title-row">'
                '<div class="login-title-icon">♙</div>'
                '<div>'
                '<div class="login-title">Selamat Datang</div>'
                '<div class="login-subtitle">'
                'Masukkan NISN untuk siswa atau NIP untuk guru.'
                '</div>'
                '</div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

            with st.form("login_form"):
                identifier = st.text_input(
                    "NISN / NIP",
                    placeholder="Masukkan NISN atau NIP",
                    key="login_identifier",
                    max_chars=20
                )
                submitted = st.form_submit_button(
                    "Masuk ke Dashboard →",
                    type="primary",
                    use_container_width=True
                )

            if not submitted:
                return

            normalized = identifier.strip()

            if not normalized:
                st.error("NISN atau NIP wajib diisi.")
                return

            # Admin: cukup ketik kata sandi admin di kolom ini
            if normalized == ADMIN_PASSWORD:
                _masuk({"nama": "Administrator"}, "Admin")
                return

            if not normalized.isdigit():
                st.error("NISN atau NIP harus berupa angka.")
                return

            guru_matches = [
                item for item in st.session_state.data["guru"]
                if str(item.get("nip", "")).strip() == normalized
                and str(item.get("nama", "")).strip()
                and str(item.get("kode", "")).strip()
            ]

            siswa_matches = [
                item for item in st.session_state.data["siswa"]
                if str(item.get("nisn", "")).strip() == normalized
                and str(item.get("nama", "")).strip()
                and str(item.get("kelas", "")).strip()
            ]

            if len(guru_matches) == 1 and len(siswa_matches) == 0:
                _masuk(guru_matches[0], "Guru")
            elif len(siswa_matches) == 1 and len(guru_matches) == 0:
                _masuk(siswa_matches[0], "Siswa")
            else:
                st.error(
                    "NISN atau NIP tidak ditemukan, datanya tidak lengkap, "
                    "atau nomor terdaftar lebih dari satu."
                )


# LOGOUT
def logout():
    for key in ["user", "role", "guru_nav", "admin_nav", "login_identifier"]:
        st.session_state.pop(key, None)

    st.session_state.screen = "login"
    st.rerun()



# ROUTING HALAMAN AWAL
if (
    st.session_state.screen != "dashboard"
    or not st.session_state.get("user")
    or not st.session_state.get("role")
):
    st.session_state.screen = "login"
    login_screen()
    st.stop()


# INFORMASI PENGGUNA
role = st.session_state.role
user = st.session_state.user

dashboard_header(user, role)

col_space, col_refresh, col_logout = st.columns([6, 2, 1])

with col_refresh:
    if st.button("Muat ulang data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop("data", None)
        st.rerun()

with col_logout:
    if st.button("Keluar", use_container_width=True):
        logout()

if role == "Admin":
    menu = [
        "Manajemen Jadwal",
        "Penugasan",
        "Monitoring Absensi",
        "Manajemen Data"
    ]

    page = st.radio(
        "Navigasi Admin",
        menu,
        horizontal=True,
        label_visibility="collapsed",
        key="admin_nav"
    )

elif role == "Guru":
    page = "Jadwal Mengajar"

else:
    page = "Jadwal Pelajaran"

st.divider()

if page == "Jadwal Pelajaran":
    page_heading(
        "Jadwal Pelajaran",
        "Lihat jadwal pelajaran sekolah." if role == "Admin" else "",
        icon="▦"
    )
elif page == "Jadwal Mengajar":
    page_heading("Jadwal Mengajar", "", icon="▦")
else:
    page_heading(page, "Kelola informasi sekolah melalui dashboard.", icon="▦")

if page == "Manajemen Jadwal":
    admin.manajemen_jadwal()

elif page == "Penugasan":
    penugasan.penugasan_guru()

elif page == "Monitoring Absensi":
    admin.monitoring_absensi()

elif page == "Manajemen Data":
    admin.manajemen_data()

elif page == "Jadwal Mengajar":
    guru.jadwal_mengajar(user)

elif page == "Jadwal Pelajaran":
    siswa.jadwal_pelajaran(user)