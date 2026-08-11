"""
climate_metrics.py
-------------------
Berechnung standortspezifischer Klimakennwerte für die Heizlastauslegung
in Anlehnung an DIN/TS 12831-1.

WICHTIG: Die exakten normativen Konventionen (Referenzperiode, Perzentil
für die Norm-Außentemperatur) sind mit dem Betreuer abzustimmen. Die hier
implementierten Defaults sind ingenieurmäßig plausible Annahmen und in der
Bachelorarbeit explizit zu begründen / ggf. anzupassen.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ClimateSummary:
    station_id: str
    reference_start: str
    reference_end: str
    n_hours: int
    jahresmitteltemperatur: float          # °C
    norm_aussentemperatur: float           # °C
    norm_perzentil: float                  # z.B. 0.001 = kältesten 0.1% der Stunden
    min_temperatur: float
    max_temperatur: float


def jahresmitteltemperatur(hourly_df: pd.DataFrame, value_col: str = "value") -> float:
    """Einfacher arithmetischer Mittelwert aller Stundenwerte im Referenzzeitraum."""
    return float(hourly_df[value_col].mean())


def norm_aussentemperatur(
    hourly_df: pd.DataFrame,
    value_col: str = "value",
    perzentil: float = 0.001,
) -> float:
    """
    Näherung der Norm-Außentemperatur über ein unteres Perzentil der
    Stundenwerte (Standard: kälteste 0,1 % der Stunden eines Jahres,
    entspricht ca. 8-9 Stunden/Jahr) statt eines einzelnen Extremwerts,
    um Ausreißer robust abzubilden.

    Hinweis: Die tatsächliche DIN/TS 12831-1-Methodik nutzt klimazonen-
    bezogene, amtlich festgelegte Auslegungstemperaturen je Landkreis.
    Diese Funktion liefert eine datengetriebene Annäherung daraus und
    sollte in der Arbeit gegen die Norm-Tabellenwerte validiert werden.
    """
    return float(hourly_df[value_col].quantile(perzentil))


def temperature_distribution(
    hourly_df: pd.DataFrame,
    value_col: str = "value",
    bin_width: float = 1.0,
) -> pd.DataFrame:
    """
    Temperaturhäufigkeitsverteilung: Stunden pro Jahr je Temperaturklasse.

    Rückgabe: DataFrame mit Spalten ['temp_bin_center', 'hours_per_year'].
    """
    values = hourly_df[value_col].dropna()
    n_years = max(
        1.0,
        (hourly_df["date"].max() - hourly_df["date"].min()).days / 365.25,
    )

    min_t = np.floor(values.min())
    max_t = np.ceil(values.max())
    bins = np.arange(min_t, max_t + bin_width, bin_width)

    counts, edges = np.histogram(values, bins=bins)
    hours_per_year = counts / n_years

    bin_centers = (edges[:-1] + edges[1:]) / 2
    return pd.DataFrame({"temp_bin_center": bin_centers, "hours_per_year": hours_per_year})


def summarize(
    hourly_df: pd.DataFrame,
    station_id: str,
    value_col: str = "value",
    perzentil: float = 0.001,
) -> ClimateSummary:
    """Fasst alle relevanten Kennwerte für einen Standort zusammen."""
    return ClimateSummary(
        station_id=station_id,
        reference_start=str(hourly_df["date"].min().date()),
        reference_end=str(hourly_df["date"].max().date()),
        n_hours=len(hourly_df),
        jahresmitteltemperatur=jahresmitteltemperatur(hourly_df, value_col),
        norm_aussentemperatur=norm_aussentemperatur(hourly_df, value_col, perzentil),
        norm_perzentil=perzentil,
        min_temperatur=float(hourly_df[value_col].min()),
        max_temperatur=float(hourly_df[value_col].max()),
    )
