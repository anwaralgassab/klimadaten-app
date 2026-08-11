# Klimadaten-App — Standortspezifische DWD-Klimadaten für die Heizsystemauslegung

Open-Source-Webapp (Python/Streamlit), die DWD-Klimadaten per PLZ-Eingabe
abruft, aufbereitet, visualisiert und über mathematische Modelle annähert —
als praxistaugliche Grundlage für die Auslegung von Wärmepumpen und
Heizsystemen (Kennwerte in Anlehnung an DIN/TS 12831-1).

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Starten

```bash
streamlit run main.py
```

Die App öffnet sich im Browser unter `http://localhost:8501`.

## Nutzung

1. PLZ eingeben (z. B. `90489` für Nürnberg)
2. Zeitraum und Perzentil für die Norm-Außentemperatur wählen
3. „Klimadaten abrufen" klicken
4. Ergebnisse in den Tabs: Übersicht, Temperaturverteilung (inkl.
   Verteilungsfit), Jahresverlauf, Rohdaten-Export (CSV)

**Hinweis:** Der erste Abruf pro Station kann je nach Datenmenge einige
Sekunden bis wenige Minuten dauern. Ergebnisse werden lokal in `.cache/`
als Parquet-Dateien zwischengespeichert, damit spätere Abfragen für dieselbe
Station sofort verfügbar sind.

## Projektstruktur

```
app/
├── main.py                    # Streamlit-Einstiegspunkt
├── modules/
│   ├── geocoding.py           # PLZ -> Koordinaten -> nächste DWD-Station
│   ├── data_fetch.py          # DWD-Datenabruf via 'wetterdienst' + Caching
│   ├── climate_metrics.py     # Kennwerte nach DIN/TS 12831-1
│   └── distribution_fit.py    # scipy.stats-Verteilungsfitting
├── tests/                     # pytest-Tests für die Berechnungslogik
├── requirements.txt
└── README.md
```

## Tests

```bash
pytest tests/ -v
```

## Datenquelle & Lizenz

- Klimadaten: © Deutscher Wetterdienst (DWD), Climate Data Center (CDC),
  bereitgestellt über [opendata.dwd.de](https://opendata.dwd.de/) und die
  Open-Source-Bibliothek [wetterdienst](https://github.com/earthobservations/wetterdienst)
- Geocoding: lokal über `pgeocode` (GeoNames-Datenbasis), keine externen
  API-Calls zur Laufzeit nötig
- Diese App: [Lizenz nach Wahl einfügen, z. B. MIT]

## Bekannte Einschränkungen / offene ToDos

- Die Norm-Außentemperatur wird aktuell datengetrieben über ein Perzentil
  angenähert. Der offizielle DIN/TS-12831-1-Wert basiert auf amtlichen,
  klimazonenbezogenen Tabellenwerten je Landkreis — ein Abgleich/eine
  Kalibrierung gegen diese Referenztabelle ist für die Bachelorarbeit
  vorzunehmen.
- Bei Stationen mit lückenhafter Historie kann die Umkreissuche in
  `geocoding.find_nearest_stations` ggf. weiter entfernte Stationen wählen
  müssen — Fallback-Strategie (z. B. Mittelung mehrerer Stationen) ist noch
  nicht implementiert.
