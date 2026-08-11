"""
Unit-Tests für climate_metrics.py.
Ausführen mit: pytest tests/
"""
import numpy as np
import pandas as pd
import pytest

from modules import climate_metrics as cm


@pytest.fixture
def synthetic_hourly_df():
    """Zwei volle Jahre stündlicher Werte mit bekanntem, konstantem Mittelwert."""
    rng = pd.date_range("2022-01-01", "2023-12-31 23:00", freq="h")
    # Konstante 10°C + kleine deterministische Schwankung, damit Mittelwert bekannt ist
    values = np.full(len(rng), 10.0)
    values[:100] = -5.0  # künstliche Kälteperiode für Perzentil-Test
    return pd.DataFrame({"date": rng, "value": values})


def test_jahresmitteltemperatur_close_to_expected(synthetic_hourly_df):
    result = cm.jahresmitteltemperatur(synthetic_hourly_df)
    # Erwartung: knapp unter 10°C wegen der 100 kalten Stunden
    assert 9.5 < result < 10.0


def test_norm_aussentemperatur_captures_cold_period(synthetic_hourly_df):
    # 100 von 17520 Stunden sind kalt (~0,57%) -> Perzentil muss darunter liegen
    result = cm.norm_aussentemperatur(synthetic_hourly_df, perzentil=0.003)
    # Die künstliche Kälteperiode muss sich im unteren Perzentil niederschlagen
    assert result < 0


def test_temperature_distribution_sums_to_hours_per_year(synthetic_hourly_df):
    dist = cm.temperature_distribution(synthetic_hourly_df, bin_width=1.0)
    total_hours = dist["hours_per_year"].sum()
    # Bei 2 Jahren Daten sollte die Summe nahe 8760 h/Jahr liegen
    assert 8700 < total_hours < 8800


def test_summarize_returns_consistent_object(synthetic_hourly_df):
    summary = cm.summarize(synthetic_hourly_df, station_id="TEST01")
    assert summary.station_id == "TEST01"
    assert summary.min_temperatur == -5.0
    assert summary.n_hours == len(synthetic_hourly_df)
