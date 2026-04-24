APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap');

:root {
    --paper: #f5efe3;
    --panel: rgba(255, 252, 247, 0.78);
    --card: #fffdfa;
    --ink: #1d2930;
    --muted: #65747c;
    --accent: #0f766e;
    --accent-deep: #134e4a;
    --accent-soft: #e6f3f0;
    --signal: #c75d1f;
    --line: #d9d2c4;
    --shadow: 0 28px 80px rgba(28, 36, 39, 0.12);
}

html, body, [class*="css"] { font-family: 'IBM Plex Sans KR', sans-serif; }

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.16), transparent 26%),
        radial-gradient(circle at top right, rgba(199, 93, 31, 0.12), transparent 24%),
        linear-gradient(180deg, #fbf8f2 0%, #f2ecdf 100%);
}

.block-container { max-width: 1320px; padding-top: 1.8rem; padding-bottom: 3rem; }

.hero-panel {
    background: linear-gradient(135deg, rgba(255,255,255,0.88) 0%, rgba(249,245,237,0.72) 100%);
    border: 1px solid rgba(217,210,196,0.92);
    border-radius: 28px;
    box-shadow: var(--shadow);
    padding: 2rem 2.2rem;
    margin-bottom: 1.4rem;
}
.hero-grid { display: grid; grid-template-columns: minmax(0,1.5fr) minmax(260px,0.85fr); gap: 1.25rem; align-items: stretch; }
.eyebrow { margin: 0 0 0.6rem 0; color: var(--signal); font-weight: 700; font-size: 0.82rem; letter-spacing: 0.16em; }
.hero-panel h1 { margin: 0; color: var(--ink); font-family: 'Fraunces', serif; font-size: clamp(2.2rem,4vw,3.8rem); line-height: 1.02; }
.hero-panel p { margin: 1rem 0 0 0; color: var(--muted); font-size: 1.03rem; line-height: 1.68; }
.hero-aside { background: rgba(15,118,110,0.08); border: 1px solid rgba(15,118,110,0.14); border-radius: 22px; padding: 1.1rem 1.2rem; }
.hero-aside h3 { margin: 0 0 0.75rem 0; color: var(--ink); font-size: 1rem; }
.hero-pills { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.hero-pills span { background: rgba(255,255,255,0.82); border: 1px solid rgba(15,118,110,0.14); color: var(--accent-deep); border-radius: 999px; padding: 0.45rem 0.85rem; font-size: 0.88rem; font-weight: 600; }

.section-title { margin: 1.25rem 0 0.75rem 0; color: var(--ink); font-family: 'Fraunces', serif; font-size: 1.6rem; }
.section-kicker { color: var(--signal); font-size: 0.85rem; font-weight: 700; letter-spacing: 0.14em; margin-bottom: 0.3rem; }
.section-note { background: var(--accent-soft); border: 1px solid rgba(15,118,110,0.14); color: var(--accent-deep); border-radius: 16px; padding: 0.75rem 0.9rem; font-size: 0.92rem; margin-bottom: 0.85rem; }
.insert-banner { background: rgba(255,249,237,0.96); border: 1px dashed rgba(199,93,31,0.34); color: #8a4216; border-radius: 16px; padding: 0.75rem 0.9rem; font-size: 0.92rem; margin-bottom: 0.85rem; }

.page-topline { display: flex; justify-content: space-between; gap: 0.75rem; align-items: center; margin-bottom: 0.55rem; }
.page-chip { display: inline-flex; align-items: center; justify-content: center; min-width: 3rem; padding: 0.35rem 0.75rem; border-radius: 999px; background: rgba(15,118,110,0.12); color: var(--accent-deep); font-weight: 700; font-size: 0.88rem; }
.source-pill { display: inline-flex; align-items: center; border-radius: 999px; background: rgba(29,41,48,0.06); color: var(--muted); padding: 0.32rem 0.6rem; font-size: 0.74rem; font-weight: 600; }
.page-meta { color: var(--ink); font-size: 0.93rem; font-weight: 600; line-height: 1.45; margin: 0.35rem 0 0.2rem 0; }
.page-submeta { color: var(--muted); font-size: 0.82rem; line-height: 1.45; margin-bottom: 0.6rem; }

.empty-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 1rem; margin-top: 1rem; }
.empty-card { background: rgba(255,255,255,0.82); border: 1px solid rgba(217,210,196,0.95); border-radius: 22px; padding: 1.35rem; min-height: 180px; box-shadow: 0 18px 44px rgba(28,36,39,0.08); }
.empty-card h3 { margin: 0.8rem 0 0.5rem 0; color: var(--ink); font-size: 1.08rem; }
.empty-card p { margin: 0; color: var(--muted); font-size: 0.94rem; line-height: 1.6; }

div[data-testid="stVerticalBlockBorderWrapper"] { background: var(--panel); border: 1px solid rgba(217,210,196,0.92); border-radius: 22px; box-shadow: 0 18px 48px rgba(28,36,39,0.08); }
div[data-testid="stMetric"] { background: rgba(255,255,255,0.72); border: 1px solid rgba(217,210,196,0.92); border-radius: 18px; padding: 0.4rem; }
div[data-testid="stMetricValue"] { color: var(--ink); }
div[data-testid="stMetricLabel"] { color: var(--muted); }
div[data-testid="stFileUploader"] { background: rgba(255,255,255,0.72); border-radius: 18px; }

.stButton > button { border-radius: 999px; border: 1px solid rgba(15,118,110,0.1); background: #eef3f2; color: var(--ink); font-weight: 600; min-height: 2.8rem; transition: all 0.18s ease; }
.stButton > button:hover { transform: translateY(-1px); border-color: rgba(15,118,110,0.28); }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #0f766e 0%, #134e4a 100%); color: white; box-shadow: 0 14px 28px rgba(15,118,110,0.2); }
.stTextInput > div > div > input, .stNumberInput input { border-radius: 14px; }
div[data-testid="stImage"] img { border-radius: 16px; border: 1px solid rgba(217,210,196,0.8); }

@media (max-width: 960px) { .hero-grid, .empty-grid { grid-template-columns: 1fr; } }

.compact-header { display: flex; justify-content: space-between; align-items: center; padding: 0.7rem 0 0.5rem 0; margin-bottom: 0.4rem; border-bottom: 1px solid var(--line); }
.app-brand { font-family: 'Fraunces', serif; font-size: 1.4rem; color: var(--ink); font-weight: 700; }
.header-stats { color: var(--muted); font-size: 0.9rem; }

.action-bar-count { display: inline-flex; align-items: center; font-weight: 700; color: var(--accent-deep); font-size: 0.95rem; padding: 0.35rem 0; }

.card-selected-bar { height: 3px; background: var(--accent); border-radius: 2px; margin: -0.25rem -0.25rem 0.5rem -0.25rem; }
.cursor-line { border-left: 3px solid var(--signal); background: rgba(199,93,31,0.06); color: #8a4216; border-radius: 0 8px 8px 0; padding: 0.45rem 0.7rem; font-size: 0.84rem; margin-top: 0.5rem; }
</style>
"""
