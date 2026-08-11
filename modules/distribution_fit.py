"""
distribution_fit.py
--------------------
Sucht die am besten passende geschlossene Verteilungsfunktion für die
Stundentemperaturwerte eines Standorts (ressourcenschonende Abbildung
statt Rohdatenspeicherung).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import warnings

from scipy import stats

# Kandidatenverteilungen: erweiterbar, bewusst überschaubar gehalten
CANDIDATE_DISTRIBUTIONS = {
    "norm": stats.norm,
    "skewnorm": stats.skewnorm,
    "weibull_min": stats.weibull_min,
    "gumbel_r": stats.gumbel_r,
    "t": stats.t,
}


@dataclass
class FitResult:
    name: str
    params: tuple
    ks_statistic: float
    ks_pvalue: float
    aic: float


def _aic(log_likelihood: float, n_params: int) -> float:
    return 2 * n_params - 2 * log_likelihood


def fit_distributions(values: pd.Series | np.ndarray) -> list[FitResult]:
    """
    Fittet alle Kandidatenverteilungen an die Daten und bewertet sie via
    Kolmogorov-Smirnov-Test und AIC. Rückgabe: Liste von FitResult,
    sortiert nach AIC (kleiner = besser).
    """
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]

    results: list[FitResult] = []

    for name, dist in CANDIDATE_DISTRIBUTIONS.items():
        try:
            params = dist.fit(values)
            log_likelihood = np.sum(dist.logpdf(values, *params))
            aic = _aic(log_likelihood, n_params=len(params))
            ks_stat, ks_p = stats.kstest(values, dist.cdf, args=params)

            results.append(
                FitResult(
                    name=name,
                    params=params,
                    ks_statistic=float(ks_stat),
                    ks_pvalue=float(ks_p),
                    aic=float(aic),
                )
            )
        except Exception as e:
            # Einzelne Verteilungen können bei bestimmten Datenformen fehlschlagen
            # (z. B. numerische Instabilität) - werden dann übersprungen, aber
            # sichtbar als Warnung ausgegeben statt stillschweigend verworfen.
            warnings.warn(f"Fit für Verteilung '{name}' fehlgeschlagen: {type(e).__name__}: {e}")
            continue

    return sorted(results, key=lambda r: r.aic)


def pdf_curve(fit_result: FitResult, x_min: float, x_max: float, n_points: int = 500):
    """Erzeugt (x, y)-Werte der gefitteten Dichtefunktion für die Visualisierung."""
    dist = CANDIDATE_DISTRIBUTIONS[fit_result.name]
    x = np.linspace(x_min, x_max, n_points)
    y = dist.pdf(x, *fit_result.params)
    return x, y
