from __future__ import annotations

import math


def approximate_significance(
    signal: float,
    background: float,
    background_fractional_uncertainty: float,
) -> float:
    if signal <= 0.0:
        return 0.0
    background = max(0.0, background)
    sigma_b = background_fractional_uncertainty * background
    variance = background + sigma_b * sigma_b
    if variance <= 0.0:
        return 0.0
    return signal / math.sqrt(variance)
