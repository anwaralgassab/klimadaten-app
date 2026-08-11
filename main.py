"""
Klimadaten-App - Open-Source-Webapp zur standortspezifischen Bereitstellung
von DWD-Klimadaten für die Auslegung von Wärmepumpen/Heizsystemen.

Start: streamlit run main.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules import climate_metrics as cm
from modules import data_fetch as df_fetch
from modules import distribution_fit as fit
from modules.geocoding import PLZNotFoundError, find_nearest_stations, plz_to_location

st.set_page_config(page_title="DWD-Klimadaten für die Heizsystemauslegung", layout="wide")

st.title("🌡️ Standortspezifische Klimadaten für die Heizsystemauslegung")
st.caption(
    "Open-Source-Tool auf Basis von DWD-Klimadaten (Deutscher Wetterdienst) — "
    "Kennwerte in Anlehnung an DIN/TS 12831-1."
)

# ---------------------------------------------------------------------------
# Sidebar: Eingaben
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Standort")
    plz = st.text_input("Postleitzahl (PLZ)", value="90489", max_chars=5)

    st.header("Zeitraum")
    col1, col2 = st.columns(2)
    start_year = col1.number_input("Start-Jahr", min_value=1990, max_value=2025, value=2014)
    end_year = col2.number_input("End-Jahr", min_value=1990, max_value=2025, value=2023)

    st.header("Auslegung")
    perzentil = st.slider(
        "Perzentil für Norm-Außentemperatur",
        min_value=0.0001, max_value=0.02, value=0.001, step=0.0001,
        format="%.4f",
        help="Anteil der kältesten Stunden eines Jahres, der zur Bestimmung "
             "der Norm-Außentemperatur herangezogen wird.",
    )

    run = st.button("Klimadaten abrufen", type="primary", use_container_width=True)

if not run:
    st.info("Bitte PLZ eingeben und 'Klimadaten abrufen' klicken.")
    st.stop()

# ---------------------------------------------------------------------------
# 1. Standort auflösen
# ---------------------------------------------------------------------------
try:
    with st.spinner("Löse PLZ auf..."):
        location = plz_to_location(plz)
except PLZNotFoundError as e:
    st.error(str(e))
    st.stop()

st.success(f"Standort: **{location.ort}** ({location.latitude:.4f}, {location.longitude:.4f})")

# ---------------------------------------------------------------------------
# 2. Nächstgelegene DWD-Station finden
# ---------------------------------------------------------------------------
try:
    with st.spinner("Suche nächstgelegene DWD-Station..."):
        stations = find_nearest_stations(location, number_of_stations=3, min_years_history=10)
except PLZNotFoundError as e:
    st.error(str(e))
    st.stop()

station_row = stations.iloc[0]
station_id = str(station_row["station_id"])

with st.expander("Verwendete DWD-Station (Details)"):
    st.dataframe(stations, use_container_width=True)

st.write(
    f"Nächstgelegene Station: **{station_row['name']}** "
    f"(ID {station_id}, Entfernung {station_row['distance']:.1f} km)"
)

# ---------------------------------------------------------------------------
# 3. Daten abrufen
# ---------------------------------------------------------------------------
try:
    with st.spinner("Lade DWD-Klimadaten (kann beim ersten Mal etwas dauern)..."):
        hourly = df_fetch.fetch_hourly_temperature(
            station_id=station_id,
            start_date=f"{start_year}-01-01",
            end_date=f"{end_year}-12-31",
        )
except Exception as e:
    st.error(f"Fehler beim DWD-Datenabruf: {e}")
    st.stop()

if hourly.empty:
    st.warning("Keine Daten für den gewählten Zeitraum verfügbar.")
    st.stop()

# ---------------------------------------------------------------------------
# 4. Kennwerte berechnen
# ---------------------------------------------------------------------------
summary = cm.summarize(hourly, station_id=station_id, perzentil=perzentil)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Übersicht", "📈 Temperaturverteilung", "🗓️ Jahresverlauf", "⬇️ Rohdaten-Export"]
)

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jahresmitteltemperatur", f"{summary.jahresmitteltemperatur:.1f} °C")
    c2.metric("Norm-Außentemperatur", f"{summary.norm_aussentemperatur:.1f} °C")
    c3.metric("Minimum", f"{summary.min_temperatur:.1f} °C")
    c4.metric("Maximum", f"{summary.max_temperatur:.1f} °C")
    st.caption(
        f"Referenzzeitraum: {summary.reference_start} bis {summary.reference_end} "
        f"({summary.n_hours:,} Stundenwerte). "
        f"Norm-Außentemperatur = {summary.norm_perzentil*100:.2f}%-Perzentil der kältesten Stunden."
    )
    st.info(
        "⚠️ Hinweis: Die Norm-Außentemperatur nach DIN/TS 12831-1 basiert offiziell auf "
        "klimazonenbezogenen Tabellenwerten je Landkreis. Der hier ausgewiesene Wert ist "
        "eine datengetriebene Annäherung und sollte damit abgeglichen werden."
    )

with tab2:
    st.subheader("Temperaturhäufigkeitsverteilung")
    dist_df = cm.temperature_distribution(hourly, bin_width=1.0)

    with st.spinner("Fitte Verteilungsfunktionen..."):
        fits = fit.fit_distributions(hourly["value"])

    fig = go.Figure()
    fig.add_bar(
        x=dist_df["temp_bin_center"], y=dist_df["hours_per_year"],
        name="Reale Verteilung (h/Jahr)", marker_color="steelblue", opacity=0.6,
    )

    if fits:
        best = fits[0]
        x, y = fit.pdf_curve(
            best, x_min=dist_df["temp_bin_center"].min(), x_max=dist_df["temp_bin_center"].max()
        )
        # Dichte in Stunden/Jahr skalieren für vergleichbare Achse
        n_years = max(1.0, (hourly["date"].max() - hourly["date"].min()).days / 365.25)
        y_scaled = y * len(hourly) / n_years
        fig.add_scatter(x=x, y=y_scaled, name=f"Modell: {best.name}", line=dict(color="crimson", width=2))

    fig.update_layout(
        xaxis_title="Außentemperatur [°C]", yaxis_title="Stunden pro Jahr",
        height=450, legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)

    if fits:
        st.subheader("Modellvergleich (beste 3 Anpassungen)")
        comparison = pd.DataFrame(
            [
                {"Verteilung": f.name, "AIC (niedriger = besser)": round(f.aic, 1),
                 "KS-Statistik": round(f.ks_statistic, 4), "KS p-Wert": round(f.ks_pvalue, 4)}
                for f in fits[:3]
            ]
        )
        st.dataframe(comparison, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Jahresverlauf (Tagesmittelwerte)")
    daily_mean = hourly.set_index("date")["value"].resample("D").mean().reset_index()
    fig2 = go.Figure()
    fig2.add_scatter(x=daily_mean["date"], y=daily_mean["value"], mode="lines",
                      line=dict(width=1, color="steelblue"))
    fig2.update_layout(xaxis_title="Datum", yaxis_title="Tagesmitteltemperatur [°C]", height=400)
    st.plotly_chart(fig2, use_container_width=True)

with tab4:
    st.subheader("Rohdaten exportieren")
    st.dataframe(hourly.head(100), use_container_width=True)
    csv = hourly.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Stundenwerte als CSV herunterladen", data=csv,
        file_name=f"klimadaten_{plz}_{station_id}.csv", mime="text/csv",
    )
