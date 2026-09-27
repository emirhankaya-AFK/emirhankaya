"""Institutional CSS theme for Document Intelligence Pipeline dashboard."""


def get_css() -> str:
    return """
<style>
/* ============================================================
   ROOT TOKENS
   ============================================================ */
:root {
  --navy-dark:   #0d1b2a;
  --navy:        #1e3a5f;
  --navy-mid:    #2c4f7c;
  --navy-light:  #3a6396;
  --accent:      #4a9eff;
  --accent-dim:  #2a6fc4;
  --success:     #27ae60;
  --warning:     #f39c12;
  --danger:      #e74c3c;
  --text-primary:   #e8edf3;
  --text-secondary: #9db4cc;
  --text-muted:     #6a8aaa;
  --border:      #2a4a6e;
  --card-bg:     #1a2f47;
  --card-bg-2:   #152538;
  --surface:     #0f1e30;
}

/* ============================================================
   GLOBAL
   ============================================================ */
[data-testid="stApp"] {
  background-color: var(--navy-dark) !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

[data-testid="stHeader"] { display: none !important; }

.block-container {
  padding-top: 1.2rem !important;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
  max-width: 1400px !important;
}

/* ============================================================
   TERMINAL HEADER
   ============================================================ */
.terminal-header {
  background: linear-gradient(135deg, var(--navy) 0%, var(--navy-mid) 100%);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 24px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.terminal-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.02em;
  white-space: nowrap;
}
.terminal-badge {
  background: var(--accent-dim);
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.05em;
  margin-left: 10px;
}
.terminal-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.meta-chip {
  background: var(--card-bg-2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 3px 10px;
}

/* ============================================================
   METRIC CARDS
   ============================================================ */
.metric-row {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.metric-card {
  flex: 1 1 160px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 18px;
  min-width: 140px;
}
.metric-card.accent { border-left: 3px solid var(--accent); }
.metric-card.success { border-left: 3px solid var(--success); }
.metric-card.warning { border-left: 3px solid var(--warning); }
.metric-card.danger  { border-left: 3px solid var(--danger); }

.metric-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 4px;
  white-space: normal;
  line-height: 1.25;
}
.metric-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}
.metric-sub {
  font-size: 0.68rem;
  color: var(--text-secondary);
  margin-top: 3px;
  white-space: normal;
  line-height: 1.3;
}

/* ============================================================
   TABS
   ============================================================ */
[data-testid="stTabs"] > div:first-child {
  background: var(--card-bg-2) !important;
  border-radius: 8px 8px 0 0 !important;
  border-bottom: 1px solid var(--border) !important;
  padding: 0 8px !important;
  gap: 2px !important;
  flex-wrap: wrap !important;
}
[data-testid="stTabs"] button {
  color: var(--text-secondary) !important;
  font-size: 0.80rem !important;
  font-weight: 500 !important;
  padding: 10px 14px !important;
  border-radius: 6px 6px 0 0 !important;
  border: none !important;
  background: transparent !important;
  white-space: nowrap !important;
}
[data-testid="stTabs"] button:hover {
  color: var(--text-primary) !important;
  background: var(--card-bg) !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--accent) !important;
  background: var(--navy-dark) !important;
  border-bottom: 2px solid var(--accent) !important;
  font-weight: 700 !important;
}

/* ============================================================
   CARDS / PANELS
   ============================================================ */
.info-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 12px;
}
.info-card h4 {
  margin: 0 0 10px 0;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}
.field-row {
  display: flex;
  gap: 8px;
  align-items: baseline;
  padding: 5px 0;
  border-bottom: 1px solid rgba(42,74,110,0.4);
  font-size: 0.85rem;
  flex-wrap: wrap;
}
.field-row:last-child { border-bottom: none; }
.field-key {
  color: var(--text-muted);
  min-width: 160px;
  font-size: 0.78rem;
}
.field-val {
  color: var(--text-primary);
  font-weight: 500;
  word-break: break-word;
}
.field-missing {
  color: var(--danger);
  font-style: italic;
  font-size: 0.78rem;
}

/* ============================================================
   EVIDENCE / CITATIONS
   ============================================================ */
.evidence-item {
  background: var(--card-bg-2);
  border-left: 3px solid var(--accent);
  border-radius: 0 6px 6px 0;
  padding: 10px 14px;
  margin-bottom: 8px;
  font-size: 0.82rem;
}
.evidence-field { color: var(--accent); font-weight: 700; font-size: 0.78rem; }
.evidence-snippet {
  color: var(--text-secondary);
  font-style: italic;
  margin: 4px 0;
  line-height: 1.4;
}
.evidence-meta { color: var(--text-muted); font-size: 0.72rem; }

/* ============================================================
   VALIDATION BADGES
   ============================================================ */
.issue-error  { color: var(--danger);  font-size: 0.82rem; padding: 3px 0; }
.issue-warning { color: var(--warning); font-size: 0.82rem; padding: 3px 0; }
.issue-ok { color: var(--success); font-size: 0.82rem; }

/* ============================================================
   FILE UPLOADER
   ============================================================ */
[data-testid="stFileUploader"] {
  background: var(--card-bg) !important;
  border: 2px dashed var(--border) !important;
  border-radius: 8px !important;
  padding: 12px !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--accent) !important;
}

/* ============================================================
   SIDEBAR
   ============================================================ */
[data-testid="stSidebar"] {
  background: var(--card-bg-2) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-secondary) !important; }

/* ============================================================
   SELECTBOX / INPUTS
   ============================================================ */
[data-testid="stSelectbox"] > div > div {
  background: var(--card-bg) !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
}

/* ============================================================
   PROGRESS / SPINNER
   ============================================================ */
[data-testid="stProgress"] > div > div {
  background: var(--accent) !important;
}

/* ============================================================
   DATAFRAME / TABLE
   ============================================================ */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}

/* ============================================================
   ALERTS
   ============================================================ */
[data-testid="stAlert"] {
  border-radius: 6px !important;
  border: 1px solid var(--border) !important;
}

/* ============================================================
   MOBILE RESPONSIVE
   ============================================================ */
@media (max-width: 768px) {
  .terminal-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 12px 16px;
  }
  .terminal-meta {
    flex-direction: column;
    gap: 6px;
  }
  .metric-row {
    flex-direction: column;
  }
  .metric-card {
    min-width: unset;
    flex: 1 1 auto;
  }
  .field-key { min-width: 120px; }
  [data-testid="stTabs"] > div:first-child {
    gap: 1px !important;
  }
  [data-testid="stTabs"] button {
    font-size: 0.72rem !important;
    padding: 8px 10px !important;
    flex: 1 1 calc(50% - 4px) !important;
    text-align: center !important;
  }
  .block-container {
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
  }
}

@media (max-width: 480px) {
  .terminal-title { font-size: 1rem; }
  [data-testid="stTabs"] button {
    font-size: 0.68rem !important;
    padding: 7px 6px !important;
  }
}
</style>
"""
