"""
data_fetch.py
-------------
Kapselt den Zugriff auf den DWD Climate Data Center (CDC) OpenData-Bestand
über die Bibliothek 'wetterdienst'. Ergebnisse werden lokal als Parquet
zwischengespeichert, um wiederholte Abfragen zu vermeiden.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from wetterdienst import Settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)


def _cache_path(station_id: str, parameter: str, resolution: str) -> Path:
    return CACHE_DIR / f"{station_id}_{resolution}_{parameter}.parquet"


def fetch_hourly_temperature(
    station_id: str,
    start_date: str = "2014-01-01",
    end_date: str = "2023-12-31",
    parameter: str = "temperature_air_mean_2m",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Lädt stündliche Lufttemperatur-Zeitreihen für eine DWD-Station.

    Rückgabe: DataFrame mit Spalten ['date', 'value'] (Temperatur in °C).
    """
    cache_file = _cache_path(station_id, parameter, "hourly")
    if use_cache and cache_file.exists():
        return pd.read_parquet(cache_file)

    settings = Settings(
        ts_shape="long",
        ts_humanize=True,
        ts_convert_units=True,  # -> SI-Einheiten, Temperatur in °C
    )

    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", parameter)],
        start_date=start_date,
        end_date=end_date,
        settings=settings,
    ).filter_by_station_id(station_id=(station_id,))

    values = next(request.values.query())
    df = values.df.to_pandas() if hasattr(values.df, "to_pandas") else values.df

    df = df[["date", "value"]].dropna(subset=["value"]).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])

    if use_cache:
        df.to_parquet(cache_file)

    return df


def fetch_daily_climate_summary(
    station_id: str,
    start_date: str = "2004-01-01",
    end_date: str = "2023-12-31",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Lädt tägliche Klimadaten (u. a. Tagesmitteltemperatur) für eine DWD-Station.

    Rückgabe: DataFrame mit Spalten ['date', 'parameter', 'value'].
    """
    cache_file = _cache_path(station_id, "climate_summary", "daily")
    if use_cache and cache_file.exists():
        return pd.read_parquet(cache_file)

    settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)

    request = DwdObservationRequest(
        parameters=[("daily", "climate_summary")],
        start_date=start_date,
        end_date=end_date,
        settings=settings,
    ).filter_by_station_id(station_id=(station_id,))

    values = next(request.values.query())
    df = values.df.to_pandas() if hasattr(values.df, "to_pandas") else values.df

    df = df.dropna(subset=["value"]).reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])

    if use_cache:
        df.to_parquet(cache_file)

    return df
