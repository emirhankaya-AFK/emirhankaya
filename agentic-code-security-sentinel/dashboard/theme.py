"""
Institutional DevSecOps Theme System & CSS Tokens.
High-density corporate security terminal aesthetic with dark navy palette and semantic indicators.
"""

import streamlit as st

# Design Tokens
BG_DARK = "#0B0F14"
SURFACE_1 = "#121923"
SURFACE_2 = "#1A2332"
SURFACE_HOVER = "#202C3E"
BORDER = "#263241"
BORDER_SOFT = "#344458"
TEXT = "#D8E2EC"
TEXT_MUTED = "#8E9BAA"
ACCENT_BLUE = "#4C8DFF"
SEMANTIC_RED = "#EF6461"
SEMANTIC_AMBER = "#E5A83A"
SEMANTIC_GREEN = "#27C281"

PLOTLY_TERMINAL_THEME = {
    "layout": {
        "paper_bgcolor": BG_DARK,
        "plot_bgcolor": SURFACE_1,
        "font": {"family": "Inter, -apple-system, sans-serif", "color": TEXT, "size": 11},
        "margin": {"l": 30, "r": 20, "t": 35, "b": 30},
        "xaxis": {
            "gridcolor": BORDER,
            "linecolor": BORDER,
            "zerolinecolor": BORDER,
            "tickfont": {"size": 10, "color": TEXT_MUTED},
        },
        "yaxis": {
            "gridcolor": BORDER,
            "linecolor": BORDER,
            "zerolinecolor": BORDER,
            "tickfont": {"size": 10, "color": TEXT_MUTED},
        },
        "legend": {
            "font": {"size": 10, "color": TEXT},
            "bgcolor": "rgba(18, 25, 35, 0.8)",
            "bordercolor": BORDER,
            "borderwidth": 1,
        },
    }
}


def inject_terminal_css():
    """Injects high-density DevSecOps terminal styling."""
    css = f"""
    <style>
    :root {{
        --bg: {BG_DARK};
        --surface-1: {SURFACE_1};
        --surface-2: {SURFACE_2};
        --surface-hover: {SURFACE_HOVER};
        --border: {BORDER};
        --border-soft: {BORDER_SOFT};
        --text: {TEXT};
        --text-muted: {TEXT_MUTED};
        --accent: {ACCENT_BLUE};
        --red: {SEMANTIC_RED};
        --amber: {SEMANTIC_AMBER};
        --green: {SEMANTIC_GREEN};
    }}

    /* Global Typography & Canvas */
    body, [class*="st-"] {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        color: var(--text);
    }}

    .stApp {{
        background-color: var(--bg) !important;
    }}

    header[data-testid="stHeader"] {{
        display: none !important;
    }}

    .block-container {{
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        min-width: 260px !important;
        max-width: 280px !important;
        background-color: var(--surface-1) !important;
        border-right: 1px solid var(--border) !important;
    }}

    [data-testid="stSidebar"] .block-container {{
        padding-top: 1.2rem !important;
        padding-left: 1.0rem !important;
        padding-right: 1.0rem !important;
    }}

    .sidebar-section-title {{
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
        margin-top: 16px;
        margin-bottom: 6px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 3px;
    }}

    /* Terminal Header Bar */
    .terminal-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px 16px;
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 9px 14px;
        margin-bottom: 12px;
        width: 100%;
        box-sizing: border-box;
    }}

    .terminal-title-group {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }}

    .terminal-title {{
        font-size: 1.10rem !important;
        font-weight: 700 !important;
        color: var(--text) !important;
        margin: 0 !important;
        padding: 0 !important;
        white-space: nowrap !important;
        line-height: 1.2 !important;
    }}

    .terminal-badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.68rem;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        white-space: nowrap;
    }}

    .badge-green {{
        background: rgba(39, 194, 129, 0.12);
        color: #27C281;
        border: 1px solid rgba(39, 194, 129, 0.3);
    }}

    .badge-blue {{
        background: rgba(76, 141, 255, 0.12);
        color: #4C8DFF;
        border: 1px solid rgba(76, 141, 255, 0.3);
    }}

    .badge-red {{
        background: rgba(239, 100, 97, 0.12);
        color: #EF6461;
        border: 1px solid rgba(239, 100, 97, 0.3);
    }}

    .badge-amber {{
        background: rgba(229, 168, 58, 0.12);
        color: #E5A83A;
        border: 1px solid rgba(229, 168, 58, 0.3);
    }}

    .header-metadata {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px 14px;
        font-size: 0.74rem;
        color: var(--text-muted);
    }}

    .meta-item {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
    }}

    .meta-value {{
        color: var(--text);
        font-weight: 600;
    }}

    /* KPI / Metric Cards */
    .metric-card {{
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 12px;
        box-sizing: border-box;
        transition: border-color 0.15s ease;
    }}

    .metric-card:hover {{
        border-color: var(--border-soft);
    }}

    .metric-label {{
        font-size: 0.70rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        margin-bottom: 4px;
        white-space: normal;
        line-height: 1.25;
        min-height: 28px;
    }}

    .metric-value {{
        font-size: 1.45rem;
        font-weight: 600;
        color: var(--text);
        letter-spacing: -0.02em;
        line-height: 1.2;
        font-variant-numeric: tabular-nums;
    }}

    .metric-sub {{
        font-size: 0.70rem;
        color: var(--text-muted);
        margin-top: 4px;
        white-space: normal;
        line-height: 1.25;
    }}

    /* Surface Card */
    .surface-card {{
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-sizing: border-box;
    }}

    .surface-card-title {{
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 8px;
    }}

    /* Agent Timeline Step Card */
    .agent-step {{
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 10px 12px;
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: 6px;
        margin-bottom: 8px;
    }}

    .agent-icon {{
        font-size: 1.1rem;
        line-height: 1;
    }}

    .agent-name {{
        font-weight: 600;
        font-size: 0.82rem;
        color: var(--accent);
    }}

    .agent-desc {{
        font-size: 0.74rem;
        color: var(--text-muted);
    }}

    /* Finding Row Card */
    .finding-card {{
        background: var(--surface-1);
        border-left: 3px solid var(--border);
        border-top: 1px solid var(--border);
        border-right: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }}

    .finding-card-critical {{
        border-left-color: var(--red) !important;
    }}

    .finding-card-high {{
        border-left-color: var(--amber) !important;
    }}

    .finding-card-medium {{
        border-left-color: #F2C94C !important;
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background-color: var(--surface-1);
        padding: 4px;
        border-radius: 8px;
        border: 1px solid var(--border);
        margin-bottom: 16px;
        flex-wrap: wrap;
        box-sizing: border-box;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 34px;
        border-radius: 6px;
        color: var(--text-muted);
        font-weight: 500;
        font-size: 0.82rem;
        padding: 0 14px;
        background-color: transparent;
        border: none;
        transition: all 0.15s ease;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--text);
        background-color: var(--surface-hover);
    }}

    .stTabs [aria-selected="true"] {{
        background-color: var(--surface-2) !important;
        color: var(--text) !important;
        font-weight: 600 !important;
        border: 1px solid var(--border) !important;
        box-shadow: none !important;
    }}

    /* Tablet Layout (max-width: 1024px) */
    @media (max-width: 1024px) {{
        .block-container {{
            padding-left: 1.0rem !important;
            padding-right: 1.0rem !important;
        }}
        .terminal-header {{
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 8px !important;
            padding: 9px 12px !important;
        }}
        .header-metadata {{
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 6px 14px !important;
            width: 100% !important;
            padding-top: 6px !important;
            border-top: 1px solid var(--border);
            font-size: 0.72rem !important;
        }}
        .metric-label {{
            font-size: 0.68rem !important;
            line-height: 1.2 !important;
        }}
        .metric-value {{
            font-size: 1.30rem !important;
        }}
    }}

    /* Mobile Layout (max-width: 768px) */
    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }}
        .terminal-header {{
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 8px !important;
            padding: 8px 10px !important;
        }}
        .header-metadata {{
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
            gap: 4px 8px !important;
            width: 100% !important;
            padding-top: 6px !important;
            border-top: 1px solid var(--border);
            font-size: 0.68rem !important;
        }}
        .meta-item {{
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            font-size: 0.68rem !important;
        }}
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
            display: flex !important;
            flex-wrap: wrap !important;
            width: 100% !important;
            gap: 4px !important;
            padding: 3px !important;
            overflow-x: visible !important;
        }}
        div[data-testid="stTabs"] [data-baseweb="tab"] {{
            flex: 1 1 calc(33.3% - 4px) !important;
            min-width: 70px !important;
            height: 28px !important;
            font-size: 0.70rem !important;
            padding: 0 4px !important;
            text-align: center !important;
            white-space: nowrap !important;
        }}
        div[data-testid="stTabs"] [data-testid="stTabsScrollRight"],
        div[data-testid="stTabs"] [data-testid="stTabsScrollLeft"] {{
            display: none !important;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
