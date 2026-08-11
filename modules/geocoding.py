"""
Geocoding-Modul
----------------
Wandelt eine deutsche Postleitzahl (PLZ) in Koordinaten um (lokal, offline,
kein externer API-Call nötig) und findet die naheliegendste(n) DWD-Station(en)
mit hinreichend langer, lückenloser Historie.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pgeocode

from wetterdienst.provider.dwd.observation import DwdObservationRequest


@dataclass
class Location:
    plz: str
    ort: str
    latitude: float
    longitude: float


class PLZNotFoundError(Exception):
    """Wird geworfen, wenn eine PLZ nicht aufgelöst werden kann."""


def plz_to_location(plz: str) -> Location:
    """Löst eine deutsche PLZ lokal (pgeocode) in Koordinaten auf."""
    nomi = pgeocode.Nominatim("de")
    result = nomi.query_postal_code(plz)

    if pd.isna(result.latitude) or pd.isna(result.longitude):
        raise PLZNotFoundError(f"PLZ '{plz}' konnte nicht aufgelöst werden.")

    return Location(
        plz=plz,
        ort=str(result.place_name),
        latitude=float(result.latitude),
        longitude=float(result.longitude),
    )


def coords_to_location(latitude: float, longitude: float) -> Location:
    """
    Erzeugt eine Location direkt aus Koordinaten (z. B. von einem Kartenklick).
    Sucht zusätzlich die nächstgelegene PLZ zur Anzeige (beste Näherung über
    die lokale pgeocode-Datenbank, kein reverse-Geocoding-Webservice nötig).
    """
    nomi = pgeocode.Nominatim("de")
    all_plz = nomi._data_frame.dropna(subset=["latitude", "longitude"])

    # Einfache euklidische Näherung reicht für die PLZ-Anzeige (kein Distanzmaß
    # mit Erdkrümmung nötig, da nur zur Beschriftung verwendet, nicht zur Berechnung)
    distances = np.sqrt(
        (all_plz["latitude"] - latitude) ** 2 + (all_plz["longitude"] - longitude) ** 2
    )
    nearest = all_plz.loc[distances.idxmin()]

    return Location(
        plz=str(nearest["postal_code"]),
        ort=str(nearest["place_name"]),
        latitude=float(latitude),
        longitude=float(longitude),
    )


def find_nearest_stations(
    location: Location,
    resolution: str = "hourly",
    dataset: str = "temperature_air",
    parameter: str = "temperature_air_mean_2m",
    number_of_stations: int = 3,
    min_years_history: int = 10,
) -> pd.DataFrame:
    """
    Findet die 'number_of_stations' nächstgelegenen DWD-Stationen zur Location,
    gefiltert auf Stationen mit ausreichend langer Historie.

    Rückgabe: DataFrame mit Stationsmetadaten (station_id, name, distance, etc.),
    sortiert nach Entfernung.
    """
    request = DwdObservationRequest(
        parameters=[(resolution, dataset, parameter)],
        periods="historical",
    )

    stations = request.filter_by_rank(
        latlon=(location.latitude, location.longitude),
        rank=number_of_stations * 4,  # größerer Pool, dann nach Historie filtern
    )

    df = stations.df.to_pandas() if hasattr(stations.df, "to_pandas") else stations.df

    if df.empty:
        raise PLZNotFoundError(
            f"Keine DWD-Station für PLZ '{location.plz}' gefunden."
        )

    df["start_date"] = pd.to_datetime(df["start_date"], utc=True, errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], utc=True, errors="coerce")
    df["history_years"] = (df["end_date"] - df["start_date"]).dt.days / 365.25

    df = df[df["history_years"] >= min_years_history].copy()
    df = df.sort_values("distance").head(number_of_stations).reset_index(drop=True)

    if df.empty:
        raise PLZNotFoundError(
            f"Keine DWD-Station mit ausreichender Historie (>= {min_years_history} "
            f"Jahre) in der Nähe von PLZ '{location.plz}' gefunden. "
            "Reduzieren Sie ggf. 'min_years_history'."
        )

    return df