from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np

from .metrics import estimate_mill_load_pct, is_successful_start, scalar_value


def compute_history_metrics(records: Sequence[dict]) -> dict:
    metrics = {
        "load_pct": [],
        "success_flags": [],
        "cascadeo": [],
        "current_pct_nominal": [],
    }
    for record in records:
        metrics["load_pct"].append(estimate_mill_load_pct(record))
        metrics["cascadeo"].append(scalar_value(record, "Ángulo (°)", "Ãngulo (Â°)", "tumblingAngle(deg)"))
        current_series = np.asarray(record.get("series", {}).get("current", []), dtype=float)
        current_series = current_series[np.isfinite(current_series)]
        metrics["current_pct_nominal"].append(np.nanmax(current_series) if current_series.size else np.nan)
        metrics["success_flags"].append(is_successful_start(record))
    return metrics


def estimated_nominal_current(records: Sequence[dict], hidden_indices: Optional[Set[int]] = None) -> float:
    hidden_indices = hidden_indices or set()
    estimates: List[float] = []
    for index, record in enumerate(records):
        if index in hidden_indices:
            continue
        imax = scalar_value(record, "I máx (Arms)", "I mÃ¡x (Arms)", "maxCurrent(Arms)")
        current_series = np.asarray(record.get("series", {}).get("current", []), dtype=float)
        current_series = current_series[np.isfinite(current_series)]
        if current_series.size == 0:
            continue
        peak_pct = float(np.nanmax(current_series))
        try:
            imax = float(imax)
        except Exception:
            continue
        if np.isnan(imax) or peak_pct <= 0:
            continue
        estimates.append(imax / (peak_pct / 100.0))
    if not estimates:
        return np.nan
    return float(np.median(estimates))


def linearity_pairs(records: Sequence[dict], x_name, y_name, hidden_indices: Optional[Set[int]] = None) -> List[Tuple[float, float, str]]:
    hidden_indices = hidden_indices or set()
    pairs = []
    x_names = x_name if isinstance(x_name, (list, tuple)) else [x_name]
    y_names = y_name if isinstance(y_name, (list, tuple)) else [y_name]
    for index, record in enumerate(records):
        if index in hidden_indices or not is_successful_start(record):
            continue
        x_value = scalar_value(record, *x_names)
        y_value = scalar_value(record, *y_names)
        try:
            x_value = float(x_value)
            y_value = float(y_value)
        except Exception:
            continue
        if np.isnan(x_value) or np.isnan(y_value):
            continue
        pairs.append((x_value, y_value, record.get("label", f"Arranque {index + 1}")))
    return pairs


def successful_speed_resistance_ratio_pairs(records: Sequence[dict], nominal_speed_rpm: float, hidden_indices: Optional[Set[int]] = None) -> List[Tuple[float, float, str]]:
    hidden_indices = hidden_indices or set()
    pairs = []
    for index, record in enumerate(records):
        if index in hidden_indices or not is_successful_start(record):
            continue
        final_speed = scalar_value(record, "Vel fin", "finalSpeed(rpm)")
        ratio_r = scalar_value(record, "Ratio R", "resRatio")
        try:
            final_speed = float(final_speed)
            ratio_r = float(ratio_r)
        except Exception:
            continue
        if np.isnan(final_speed) or np.isnan(ratio_r) or not nominal_speed_rpm:
            continue
        speed_ratio = final_speed / nominal_speed_rpm
        if np.isnan(speed_ratio):
            continue
        pairs.append((ratio_r, speed_ratio, record.get("label", f"Arranque {index + 1}")))
    return pairs


def successful_current_analysis_pairs(records: Sequence[dict], nominal_current: float, hidden_indices: Optional[Set[int]] = None) -> List[Tuple[float, float, str, int]]:
    hidden_indices = hidden_indices or set()
    pairs = []
    if np.isnan(nominal_current) or nominal_current <= 0:
        return pairs
    for index, record in enumerate(records):
        if index in hidden_indices or not is_successful_start(record):
            continue
        init_current = scalar_value(record, "I inicial", "initCurrent(Arms)")
        short_current = scalar_value(record, "I cortoc (A)", "I cortoc", "maxShortCurr(A)")
        try:
            init_current = float(init_current)
            short_current = float(short_current)
        except Exception:
            continue
        if np.isnan(init_current) or np.isnan(short_current):
            continue
        init_pct = 100.0 * init_current / nominal_current
        short_pct = 100.0 * short_current / nominal_current
        if np.isnan(init_pct) or np.isnan(short_pct):
            continue
        pairs.append((init_pct, short_pct, record.get("label", f"Arranque {index + 1}"), index))
    return pairs
