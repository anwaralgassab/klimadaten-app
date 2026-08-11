"""
Live-Test: echter Abruf von PLZ -> Station -> DWD-Klimadaten.
Ausführen mit: python test_live_dwd.py
"""
from modules.geocoding import plz_to_location, find_nearest_stations
from modules.data_fetch import fetch_hourly_temperature
from modules import climate_metrics as cm

PLZ = "90489"  # Nürnberg, ggf. anpassen

print(f"1) Löse PLZ {PLZ} auf...")
location = plz_to_location(PLZ)
print(f"   -> {location}")

print("\n2) Suche nächstgelegene DWD-Station(en)...")
stations = find_nearest_stations(location, number_of_stations=3, min_years_history=10)
print(stations[["station_id", "name", "distance", "start_date", "end_date"]])

station_id = str(stations.iloc[0]["station_id"])
print(f"\n3) Lade stündliche Temperaturdaten für Station {station_id}...")
print("   (kann beim ersten Mal 10-60 Sekunden dauern)")
hourly = fetch_hourly_temperature(
    station_id=station_id,
    start_date="2020-01-01",
    end_date="2023-12-31",
)
print(f"   -> {len(hourly)} Stundenwerte geladen")
print(hourly.head())
print(hourly.tail())

print("\n4) Berechne Klimakennwerte...")
summary = cm.summarize(hourly, station_id=station_id)
print(summary)

print("\n✅ Live-Test erfolgreich abgeschlossen.")