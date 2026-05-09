APP_CSS = """
<style>
:root {
    --bg: #f7f8fa;
    --surface: #ffffff;
    --ink: #1f2937;
    --muted: #687385;
    --line: #d9dee7;
    --accent: #2563eb;
    --accent-soft: #eff6ff;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: var(--bg);
}

.block-container {
    max-width: 1180px;
    padding-top: 1.4rem;
    padding-bottom: 2.5rem;
}

.topbar {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1rem;
    padding-bottom: 0.9rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid var(--line);
}

.app-brand {
    color: var(--ink);
    font-size: 1.55rem;
    font-weight: 750;
    line-height: 1.2;
}

.app-subtitle,
.header-stats {
    color: var(--muted);
    font-size: 0.92rem;
}

.app-subtitle {
    margin-top: 0.2rem;
}

.section-title {
    color: var(--ink);
    font-size: 1.05rem;
    font-weight: 750;
    margin: 1.2rem 0 0.55rem 0;
}

.selected-count,
.page-window {
    color: var(--ink);
    font-size: 0.92rem;
    font-weight: 700;
    padding: 0.55rem 0;
}

.page-window {
    text-align: center;
}

.page-window span {
    color: var(--muted);
    display: block;
    font-size: 0.8rem;
    font-weight: 500;
    margin-top: 0.1rem;
}

.page-topline {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.page-number {
    align-items: center;
    background: var(--accent-soft);
    border: 1px solid #c8dbff;
    border-radius: 6px;
    color: #174ea6;
    display: inline-flex;
    font-size: 0.88rem;
    font-weight: 750;
    justify-content: center;
    min-width: 2.25rem;
    padding: 0.25rem 0.45rem;
}

.source-kind {
    color: var(--muted);
    font-size: 0.74rem;
    font-weight: 700;
}

.page-meta {
    color: var(--ink);
    font-size: 0.9rem;
    font-weight: 650;
    line-height: 1.35;
    margin-top: 0.45rem;
    overflow-wrap: anywhere;
}

.page-submeta {
    color: var(--muted);
    font-size: 0.78rem;
    line-height: 1.35;
    margin-bottom: 0.55rem;
}

.card-selected-bar {
    background: var(--accent);
    border-radius: 4px;
    height: 3px;
    margin-bottom: 0.5rem;
}

.empty-state {
    border: 1px dashed var(--line);
    border-radius: 8px;
    color: var(--muted);
    font-size: 0.95rem;
    margin-top: 1rem;
    padding: 1.4rem;
    text-align: center;
}

.button-spacer {
    height: 1.75rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    box-shadow: none;
}

div[data-testid="stFileUploader"] {
    background: #fbfcfe;
    border-radius: 8px;
}

div[data-testid="stImage"] img {
    border: 1px solid var(--line);
    border-radius: 6px;
}

.stButton > button {
    border: 1px solid var(--line);
    border-radius: 6px;
    color: var(--ink);
    font-weight: 650;
    min-height: 2.45rem;
}

.stButton > button[kind="primary"] {
    background: var(--accent);
    border-color: var(--accent);
    color: #ffffff;
}

.stTextInput > div > div > input,
.stNumberInput input {
    border-radius: 6px;
}

@media (max-width: 860px) {
    .topbar {
        align-items: flex-start;
        flex-direction: column;
    }

    .header-stats {
        font-size: 0.86rem;
    }
}
</style>
"""
