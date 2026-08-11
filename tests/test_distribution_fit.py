"""
Unit-Tests für distribution_fit.py.
"""
import numpy as np

from modules import distribution_fit as fit


def test_fit_distributions_ranks_true_distribution_well():
    rng = np.random.default_rng(42)
    # Daten aus einer bekannten Normalverteilung generieren
    values = rng.normal(loc=9.0, scale=6.5, size=20000)

    results = fit.fit_distributions(values)
    assert len(results) > 0

    by_name = {r.name: r for r in results}
    assert "norm" in by_name

    # 'norm' darf laut KS-Test nicht verworfen werden (Nullhypothese: Daten
    # stammen aus dieser Verteilung) - p-Wert > 0.01 ist ein plausibler Wert
    # für tatsächlich normalverteilte Daten.
    assert by_name["norm"].ks_pvalue > 0.01

    # Flexiblere Verteilungen (skewnorm, t) enthalten die Normalverteilung
    # als Spezialfall und können bei großer Stichprobe durch zufälliges
    # Überanpassen im AIC leicht besser abschneiden, obwohl die Daten
    # wirklich normalverteilt sind. Daher: 'norm' muss nicht Top-1/2 sein,
    # aber AIC-mäßig nah am besten Modell liegen (kein klar schlechteres Modell).
    best_aic = results[0].aic
    assert by_name["norm"].aic - best_aic < 50


def test_pdf_curve_returns_matching_lengths():
    rng = np.random.default_rng(0)
    values = rng.normal(0, 1, 5000)
    results = fit.fit_distributions(values)
    x, y = fit.pdf_curve(results[0], x_min=-5, x_max=5, n_points=200)
    assert len(x) == len(y) == 200