from __future__ import annotations

from typing import Mapping

import numpy as np

from .models import StartupRecord, StartupSeries
from .startup_detection import normalize_header


def _record_scalars(record) -> Mapping:
    if isinstance(record, StartupRecord):
        return record.scalars
    return record.get("scalars", {})


def _record_series(record):
    if isinstance(record, StartupRecord):
        return record.series
    return record.get("series", {})


def _series_array(series, name: str) -> np.ndarray:
    if isinstance(series, StartupSeries):
        return np.asarray(getattr(series, name), dtype=float)
    return np.asarray(series.get(name, []), dtype=float)


def scalar_value(record, *names):
    scalars = _record_scalars(record)
    normalized = {normalize_header(key): value for key, value in scalars.items()}
    for name in names:
        if name in scalars:
            return scalars[name]
        key = normalize_header(name)
        if key in normalized:
            return normalized[key]
        for normalized_name, value in normalized.items():
            if key and (key in normalized_name or normalized_name in key):
                return value
    return np.nan


def is_successful_start(record) -> bool:
    if isinstance(record, StartupRecord):
        start_type = record.start_type
    else:
        start_type = record.get("start_type", "")
    return "successful" in str(start_type).strip().lower()


def is_externally_aborted_start(record) -> bool:
    if isinstance(record, StartupRecord):
        start_type = record.start_type
    else:
        start_type = record.get("start_type", "")
    return "externally aborted" in str(start_type).strip().lower()


def estimate_mill_load_pct(record) -> float:
    load_torque = _series_array(_record_series(record), "load_torque")
    load_torque = load_torque[np.isfinite(load_torque)]

    amp_frozen = scalar_value(record, "Amp frz(%)", "frzChrgAmp(%FLT)")
    try:
        amp_frozen = float(amp_frozen)
    except Exception:
        amp_frozen = np.nan

    if load_torque.size == 0:
        if np.isnan(amp_frozen):
            return np.nan
        return float(np.clip(amp_frozen, 0.0, 100.0))

    angles = np.linspace(0.0, 180.0, load_torque.size)
    stationary_mask = angles >= 150.0
    stationary_torque = load_torque[stationary_mask]
    stationary_torque = stationary_torque[np.isfinite(stationary_torque)]

    if stationary_torque.size < 5:
        tail_count = max(5, int(round(load_torque.size * 0.15)))
        stationary_torque = load_torque[-tail_count:]
        stationary_torque = stationary_torque[np.isfinite(stationary_torque)]

    if stationary_torque.size == 0:
        if np.isnan(amp_frozen):
            return np.nan
        return float(np.clip(amp_frozen, 0.0, 100.0))

    steady_resistant_torque = float(np.nanmedian(stationary_torque))
    if np.isnan(steady_resistant_torque):
        return np.nan

    if np.isnan(amp_frozen) or amp_frozen <= 0:
        return float(np.clip(steady_resistant_torque, 0.0, 100.0))

    estimated_load_pct = 100.0 * steady_resistant_torque / amp_frozen
    return float(np.clip(estimated_load_pct, 0.0, 100.0))
