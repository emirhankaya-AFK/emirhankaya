"""
Institutional Risk Terminal - Design System & Theme Tokens
==========================================================
Clean, high-density corporate finance & risk management design system:
- Dark navy-slate / obsidian palette (#0B0F14, #121923, #17212D)
- Interactive accent: Institutional Blue (#4C8DFF)
- Semantic accents: Gain (#27C281), Loss (#EF6461), Caution (#E5A83A), Info (#42B8D5)
- Tabular numeric alignment (tabular-nums) for institutional financial readability
- Unified Plotly theme matching the design system
"""

THEME_COLORS = {
    "bg": "#0B0F14",
    "sidebar": "#0E141C",
    "surface_1": "#121923",
    "surface_2": "#17212D",
    "surface_hover": "#1D2A38",
    "border": "#263241",
    "border_soft": "#1D2733",
    "text": "#E7EDF4",
    "text_muted": "#8E9BAA",
    "primary": "#4C8DFF",
    "primary_soft": "rgba(76, 141, 255, 0.14)",
    "positive": "#27C281",
    "warning": "#E5A83A",
    "negative": "#EF6461",
    "info": "#42B8D5",
}

# Color sequence for multi-asset charts (colorblind-accessible institutional palette)
CHART_COLOR_PALETTE = [
    "#4C8DFF",  # Primary Blue (BIST 100)
    "#27C281",  # Teal / Emerald (S&P 500)
    "#E5A83A",  # Amber / Gold (Gold)
    "#42B8D5",  # Cyan (Eurobond)
    "#6366F1",  # Indigo (TRY Deposit / Cash)
    "#F43F5E",  # Rose (Brent Oil)
    "#8B5CF6",  # Violet (Global Aggregate)
    "#10B981"   # Mint (US Treasury)
]

PLOTLY_TERMINAL_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#121923",
    font=dict(color="#8E9BAA", family="Inter, system-ui, -apple-system, sans-serif", size=11),
    margin=dict(l=35, r=20, t=35, b=35),
    colorway=CHART_COLOR_PALETTE,
    xaxis=dict(
        gridcolor="rgba(142, 155, 170, 0.12)",
        zerolinecolor="rgba(142, 155, 170, 0.22)",
        tickfont=dict(color="#8E9BAA", size=11),
        title_font=dict(color="#E7EDF4", size=11)
    ),
    yaxis=dict(
        gridcolor="rgba(142, 155, 170, 0.12)",
        zerolinecolor="rgba(142, 155, 170, 0.22)",
        tickfont=dict(color="#8E9BAA", size=11),
        title_font=dict(color="#E7EDF4", size=11)
    ),
    hoverlabel=dict(
        bgcolor="#17212D",
        bordercolor="#263241",
        font=dict(color="#E7EDF4", family="Inter, sans-serif", size=11)
    )
)

TERMINAL_CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #0B0F14;
        --sidebar: #0E141C;
        --surface-1: #121923;
        --surface-2: #17212D;
        --surface-hover: #1D2A38;
        --border: #263241;
        --border-soft: #1D2733;
        --text: #E7EDF4;
        --text-muted: #8E9BAA;
        --primary: #4C8DFF;
        --primary-soft: rgba(76, 141, 255, 0.14);
        --positive: #27C281;
        --warning: #E5A83A;
        --negative: #EF6461;
        --info: #42B8D5;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--text);
        background-color: var(--bg) !important;
    }

    .stApp {
        background-color: var(--bg) !important;
    }

    /* Streamlit Main Container Spacing */
    .block-container {
        padding-top: 1.0rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }

    /* Narrow, structured sidebar (256px desktop width) */
    [data-testid="stSidebar"] {
        min-width: 248px !important;
        max-width: 264px !important;
        background-color: var(--sidebar) !important;
        border-right: 1px solid var(--border-soft) !important;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-left: 0.9rem !important;
        padding-right: 0.9rem !important;
    }

    /* Sidebar Section Headers */
    .sidebar-section-title {
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
        margin-top: 16px;
        margin-bottom: 6px;
        border-bottom: 1px solid var(--border-soft);
        padding-bottom: 3px;
    }

    /* Top Bar Header */
    .terminal-header {
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
    }

    .terminal-title-group {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }

    .terminal-title {
        font-size: 1.08rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        color: var(--text) !important;
        margin: 0 !important;
        padding: 0 !important;
        white-space: nowrap !important;
        line-height: 1.2 !important;
    }

    .terminal-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.68rem;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.02em;
        white-space: nowrap;
    }

    .terminal-badge-live {
        background: rgba(39, 194, 129, 0.12);
        color: #27C281;
        border: 1px solid rgba(39, 194, 129, 0.3);
    }

    .terminal-badge-synthetic {
        background: rgba(229, 168, 58, 0.12);
        color: #E5A83A;
        border: 1px solid rgba(229, 168, 58, 0.3);
    }

    .terminal-badge-info {
        background: rgba(76, 141, 255, 0.10);
        color: #8E9BAA;
        border: 1px solid var(--border);
    }

    .header-metadata {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px 14px;
        font-size: 0.74rem;
        color: var(--text-muted);
    }

    .meta-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
    }

    .meta-label {
        color: var(--text-muted);
    }

    .meta-value {
        color: var(--text);
        font-weight: 600;
    }

    /* KPI / Metric Cards */
    .metric-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 12px;
        transition: border-color 0.15s ease;
        box-sizing: border-box;
    }

    .metric-card:hover {
        border-color: var(--border-soft);
    }

    .metric-label {
        font-size: 0.70rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        margin-bottom: 4px;
        white-space: normal;
        line-height: 1.25;
        min-height: 28px;
    }

    .metric-value {
        font-size: 1.45rem;
        font-weight: 600;
        color: var(--text);
        letter-spacing: -0.02em;
        line-height: 1.2;
        font-variant-numeric: tabular-nums;
    }

    .metric-sub {
        font-size: 0.70rem;
        color: var(--text-muted);
        margin-top: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Formula & Section Cards */
    .surface-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-sizing: border-box;
    }

    .surface-card-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 6px;
    }

    /* Tab Styling - Clean, Monochromatic with Blue Accent */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: var(--surface-1);
        padding: 4px;
        border-radius: 8px;
        border: 1px solid var(--border);
        margin-bottom: 16px;
        flex-wrap: wrap;
        box-sizing: border-box;
    }

    .stTabs [data-baseweb="tab"] {
        height: 34px;
        border-radius: 6px;
        color: var(--text-muted);
        font-weight: 500;
        font-size: 0.82rem;
        padding: 0 14px;
        background-color: transparent;
        border: none;
        transition: all 0.15s ease;
        box-sizing: border-box;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text);
        background-color: var(--surface-hover);
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--surface-2) !important;
        color: var(--text) !important;
        font-weight: 600 !important;
        border: 1px solid var(--border) !important;
        box-shadow: none !important;
    }

    /* Dataframe and Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
    }

    /* Hide Streamlit default header decoration */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Slider & Form Inputs */
    .stSlider [data-baseweb="slider"] {
        margin-top: 4px;
    }

    /* Utility status dot */
    .status-dot-green {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #27C281;
        margin-right: 5px;
    }

    /* Tablet Layout (max-width: 1024px) */
    @media (max-width: 1024px) {
        .block-container {
            padding-left: 1.0rem !important;
            padding-right: 1.0rem !important;
        }
        .terminal-header {
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 8px !important;
            padding: 9px 12px !important;
        }
        .terminal-title-group {
            width: 100% !important;
        }
        .header-metadata {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 6px 14px !important;
            width: 100% !important;
            padding-top: 6px !important;
            border-top: 1px solid var(--border-soft) !important;
            font-size: 0.72rem !important;
        }
        .metric-label {
            font-size: 0.68rem !important;
            line-height: 1.2 !important;
        }
        .metric-value {
            font-size: 1.30rem;
        }
    }

    /* Mobile Layout (max-width: 768px, e.g. 390x844) */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }
        .terminal-header {
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 8px !important;
            padding: 8px 10px !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        .terminal-title-group {
            display: flex !important;
            align-items: center !important;
            flex-wrap: wrap !important;
            gap: 6px !important;
            width: 100% !important;
        }
        .terminal-title {
            font-size: 0.98rem !important;
        }
        .header-metadata {
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
            gap: 4px 8px !important;
            width: 100% !important;
            box-sizing: border-box !important;
            padding-top: 6px !important;
            border-top: 1px solid var(--border-soft) !important;
            font-size: 0.68rem !important;
        }
        .meta-item {
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            font-size: 0.68rem !important;
        }

        /* Tabs on Mobile: 2-Row Wrap, zero scroll, 100% visible */
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            display: flex !important;
            flex-wrap: wrap !important;
            width: 100% !important;
            height: auto !important;
            box-sizing: border-box !important;
            gap: 4px !important;
            padding: 3px !important;
            overflow-x: visible !important;
        }
        div[data-testid="stTabs"] [data-baseweb="tab"] {
            flex: 1 1 calc(33.3% - 4px) !important;
            min-width: 70px !important;
            max-width: 100% !important;
            height: 28px !important;
            font-size: 0.70rem !important;
            padding: 0 4px !important;
            justify-content: center !important;
            text-align: center !important;
            white-space: nowrap !important;
            box-sizing: border-box !important;
        }
        div[data-testid="stTabs"] [data-testid="stTabsScrollRight"],
        div[data-testid="stTabs"] [data-testid="stTabsScrollLeft"] {
            display: none !important;
        }
        div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
        div[data-testid="stTabs"] [data-baseweb="tab-border"] {
            display: none !important;
        }
    }
</style>
"""
