"""
styling.py
-----------
Zentrales Design-Modul der App. Definiert die Farbpalette, Typografie und
Mikro-Animationen als CSS, das in main.py per st.markdown injiziert wird.

Design-Idee: Die App visualisiert Temperaturspannen - deshalb zieht sich ein
Kalt-Warm-Gradient (Stahlblau -> Kupfer) als wiederkehrendes Signatur-Element
durch Kennwert-Karten, Kopfzeile und Diagramme.
"""

# Zentrale Design-Tokens - hier lässt sich das ganze Farbschema anpassen
COLORS = {
    "bg_primary": "#10161D",
    "bg_panel": "#1A232C",
    "bg_panel_light": "#212C37",
    "border": "#2A3540",
    "text_primary": "#EDEFF2",
    "text_muted": "#8B96A3",
    "accent_cold": "#4C8DC0",
    "accent_warm": "#E28743",
}

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {{
    --bg-primary: {COLORS['bg_primary']};
    --bg-panel: {COLORS['bg_panel']};
    --bg-panel-light: {COLORS['bg_panel_light']};
    --border: {COLORS['border']};
    --text-primary: {COLORS['text_primary']};
    --text-muted: {COLORS['text_muted']};
    --accent-cold: {COLORS['accent_cold']};
    --accent-warm: {COLORS['accent_warm']};
    --gradient: linear-gradient(90deg, var(--accent-cold) 0%, var(--accent-warm) 100%);
}}

/* Grundlayout */
.stApp {{
    background-color: var(--bg-primary);
    font-family: 'IBM Plex Sans', sans-serif;
}}

/* Überschriften in der Display-Schrift */
h1, h2, h3 {{
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.01em;
}}

/* Sidebar als "Kontrollpanel" */
[data-testid="stSidebar"] {{
    background-color: var(--bg-panel);
    border-right: 1px solid var(--border);
}}
[data-testid="stSidebar"] h2 {{
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-top: 1.5rem;
}}

/* Signatur-Element: Gradient-Linie unter dem Haupttitel */
.app-header {{
    animation: fadeSlideIn 0.6s ease-out;
}}
.app-header .gradient-rule {{
    height: 3px;
    width: 100%;
    background: var(--gradient);
    border-radius: 2px;
    margin: 0.75rem 0 1.5rem 0;
}}

/* Kennwert-Karten mit Gradient-Akzent (ersetzt Standard st.metric-Look) */
.metric-card {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    position: relative;
    overflow: hidden;
    animation: fadeSlideIn 0.6s ease-out backwards;
    transition: transform 0.15s ease, border-color 0.15s ease;
}}
.metric-card:hover {{
    transform: translateY(-2px);
    border-color: var(--accent-cold);
}}
.metric-card::before {{
    content: "";
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: var(--gradient);
}}
.metric-card .label {{
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}}
.metric-card .value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.9rem;
    font-weight: 600;
    color: var(--text-primary);
}}

/* Gestaffeltes Einblenden für mehrere Karten nebeneinander */
.metric-card:nth-child(1) {{ animation-delay: 0.05s; }}
.metric-card:nth-child(2) {{ animation-delay: 0.12s; }}
.metric-card:nth-child(3) {{ animation-delay: 0.19s; }}
.metric-card:nth-child(4) {{ animation-delay: 0.26s; }}

@keyframes fadeSlideIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

@media (prefers-reduced-motion: reduce) {{
    .app-header, .metric-card {{ animation: none; }}
}}

/* Tabs im Panel-Stil */
[data-testid="stTabs"] button {{
    font-family: 'Space Grotesk', sans-serif;
    color: var(--text-muted);
}}
[data-testid="stTabs"] button[aria-selected="true"] {{
    color: var(--text-primary);
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    background: var(--gradient) !important;
}}

/* Primärer Button mit Gradient */
button[kind="primary"] {{
    background: var(--gradient) !important;
    border: none !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: opacity 0.15s ease, transform 0.15s ease;
}}
button[kind="primary"]:hover {{
    opacity: 0.9;
    transform: translateY(-1px);
}}

/* Monospace für Datentabellen und Kennzahlen-Kontext */
[data-testid="stDataFrame"] {{
    font-family: 'IBM Plex Mono', monospace;
}}

/* Hinweisboxen etwas ruhiger einfärben */
[data-testid="stAlert"] {{
    border-radius: 8px;
}}
</style>
"""


def inject() -> str:
    """Gibt das CSS zurück, wird via st.markdown(styling.inject(), unsafe_allow_html=True) eingebunden."""
    return CUSTOM_CSS


def metric_card_html(label: str, value: str) -> str:
    """Erzeugt eine einzelne gestylte Kennwert-Karte als HTML (Ersatz für st.metric)."""
    return f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
    </div>
    """


def header_html(title: str, caption: str) -> str:
    """Erzeugt die Kopfzeile mit dem Gradient-Signatur-Element."""
    return f"""
    <div class="app-header">
        <h1 style="margin-bottom:0;">{title}</h1>
        <p style="color:var(--text-muted); margin-top:0.4rem;">{caption}</p>
        <div class="gradient-rule"></div>
    </div>
    """


def plotly_theme() -> dict:
    """Gemeinsames Farbschema für Plotly-Diagramme, passend zum App-Design."""
    return dict(
        paper_bgcolor=COLORS["bg_primary"],
        plot_bgcolor=COLORS["bg_panel"],
        font=dict(family="IBM Plex Sans, sans-serif", color=COLORS["text_primary"]),
        xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
    )