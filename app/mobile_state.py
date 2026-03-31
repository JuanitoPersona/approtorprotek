from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Callable, List, Optional

import numpy as np

from .csv_loader import parse_csv_dataset, read_csv_rows
from .historical import (
    compute_history_metrics,
    estimated_nominal_current,
    linearity_pairs,
    successful_current_analysis_pairs,
    successful_speed_resistance_ratio_pairs,
)
from .metrics import scalar_value
from .metrics import is_successful_start
from .models import StartupDataset, StartupRecord

MAX_CSV_SIZE_BYTES = 64 * 1024 * 1024


@dataclass
class MobileAppState:
    current_file: str = ""
    current_file_label: str = ""
    dataset: Optional[StartupDataset] = None
    selected_start_index: int = 0
    cm_main_metrics: List[str] = field(default_factory=lambda: ["Duración (s)"])
    cm_secondary_metrics: List[str] = field(default_factory=lambda: ["I máx (Arms)"])
    cm_success_only: bool = False
    show_harmonics: bool = True
    validation_messages: List[str] = field(default_factory=list)
    last_load_ok: bool = False
    load_progress: int = 0

    @property
    def has_dataset(self) -> bool:
        return self.dataset is not None and bool(self.dataset.records)

    @property
    def is_multi(self) -> bool:
        return self.has_dataset and len(self.dataset.records) > 1

    @property
    def records(self) -> List[StartupRecord]:
        return list(self.dataset.records) if self.dataset else []

    def load_csv(
        self,
        file_path: str,
        display_name: str | None = None,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> tuple[bool, str]:
        self.current_file = file_path
        self.current_file_label = display_name or os.path.basename(file_path)
        self.selected_start_index = 0
        self.cm_main_metrics = ["Duración (s)"]
        self.cm_secondary_metrics = ["I máx (Arms)"]
        self.cm_success_only = False
        self.show_harmonics = True
        self.last_load_ok = False
        self.load_progress = 0
        self._report_progress(progress_callback, 1, "Validando archivo...")
        if not os.path.exists(file_path):
            self.dataset = None
            self.validation_messages = ["El archivo seleccionado ya no existe o no se puede abrir."]
            return False, self.validation_messages[0]

        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            file_size = -1

        if file_size == 0:
            self.dataset = None
            self.validation_messages = ["El archivo seleccionado esta vacio."]
            return False, self.validation_messages[0]

        if file_size > MAX_CSV_SIZE_BYTES:
            self.dataset = None
            self.validation_messages = [
                "El archivo seleccionado es demasiado grande para abrirlo con seguridad en el movil."
            ]
            return False, self.validation_messages[0]

        try:
            rows = read_csv_rows(
                file_path,
                progress_callback=lambda ratio, text: self._report_progress(
                    progress_callback, int(min(90, max(1, round(ratio * 100)))), text
                ),
            )
            self._report_progress(progress_callback, 94, "Interpretando estructura de arranques...")
            dataset = parse_csv_dataset(rows)
        except Exception as exc:
            self.dataset = None
            self.validation_messages = [f"No se pudo leer el archivo: {exc}"]
            return False, self.validation_messages[0]

        self.dataset = dataset
        self.validation_messages = list(dataset.validation_issues)
        if not dataset.records:
            return False, dataset.validation_issues[0] if dataset.validation_issues else "No se detectaron arranques validos."

        self.last_load_ok = True
        self.load_progress = 100
        self._report_progress(progress_callback, 100, "Archivo cargado correctamente.")
        mode_label = "multiarranque" if len(dataset.records) > 1 else "arranque unico"
        source_label = "XLSX" if file_path.lower().endswith(".xlsx") else "CSV"
        return True, f"{source_label} cargado: {len(dataset.records)} arranque(s), modo {mode_label}."

    def _report_progress(self, callback: Callable[[int, str], None] | None, percent: int, text: str):
        percent = max(0, min(100, int(percent)))
        self.load_progress = percent
        if callback is not None:
            callback(percent, text)

    def current_record(self) -> Optional[StartupRecord]:
        if not self.records:
            return None
        index = min(max(self.selected_start_index, 0), len(self.records) - 1)
        return self.records[index]

    def current_record_index(self) -> int:
        if not self.records:
            return 0
        return min(max(self.selected_start_index, 0), len(self.records) - 1)

    def startup_labels(self) -> List[str]:
        return [record.label for record in self.records]

    def viewer_header_payload(self, record: Optional[StartupRecord]) -> dict:
        if record is None:
            return {
                "title": "Visualizacion de Arranque",
                "subtitle": "Carga un CSV para inspeccionar un arranque.",
                "selection_text": "Sin arranque activo",
                "dataset_text": "Sin dataset",
            }

        total = len(self.records)
        index = self.current_record_index()
        if total > 1:
            selection_text = f"Arranque {index + 1} de {total}"
            subtitle = "Vista movil del arranque activo dentro del conjunto cargado."
        else:
            selection_text = "Arranque unico"
            subtitle = "Vista movil del unico arranque detectado en el CSV."

        source_label = "CSV multiarranque" if record.source_kind == "multi_file" else "CSV arranque unico"
        return {
            "title": "Visualizacion de Arranque",
            "subtitle": subtitle,
            "selection_text": selection_text,
            "dataset_text": source_label,
        }

    def viewer_detail_rows(self, record: Optional[StartupRecord]) -> List[tuple[str, str]]:
        if record is None:
            return []
        return [
            ("Fecha", record.timestamp_text or "Sin fecha"),
            ("Tipo", record.start_type or "Unknown"),
            ("Proteccion", record.protection or "Unknown"),
            ("Descripcion", record.description or "Sin descripcion"),
        ]

    def viewer_metric_cards(self, record: Optional[StartupRecord]) -> List[tuple[str, str]]:
        if record is None:
            return []
        scalars = record.scalars
        return [
            ("Duración", _format_scalar(scalars.get("Duración (s)"), "s")),
            ("I máx", _format_scalar(scalars.get("I máx (Arms)"), "A")),
            ("Vel. final", _format_scalar(scalars.get("Vel fin"), "rpm")),
            ("Tipo", record.start_type or "Unknown"),
        ]

    def viewer_secondary_metrics(self, record: Optional[StartupRecord]) -> List[tuple[str, str]]:
        if record is None:
            return []
        scalars = record.scalars
        return [
            ("Tiempo I max", _format_scalar(scalars.get("Tiempo I m\xE1x (s)"), "s")),
            ("Par max", _format_scalar(scalars.get("Par m\xE1x (%)"), "%")),
            ("Energia", _format_scalar(scalars.get("E dis(MJ)"), "MJ")),
            ("Angulo", _format_scalar(scalars.get("\xC1ngulo (\xB0)"), "deg")),
        ]

    def condition_monitoring_series(self, metric_name: str) -> tuple[list[tuple[float, float]], int]:
        points: list[tuple[float, float]] = []
        omitted = 0
        filtered_indices = self.condition_monitoring_filtered_indices()
        for filtered_pos, index in enumerate(filtered_indices):
            record = self.records[index]
            value = scalar_value(record.to_legacy(), metric_name)
            try:
                numeric = float(value)
            except Exception:
                omitted += 1
                continue
            if np.isnan(numeric):
                omitted += 1
                continue
            points.append((float(filtered_pos), numeric))
        return points, omitted

    def toggle_cm_success_only(self):
        self.cm_success_only = not self.cm_success_only

    def condition_monitoring_filtered_indices(self) -> List[int]:
        if not self.cm_success_only:
            return list(range(len(self.records)))
        return [index for index, record in enumerate(self.records) if is_successful_start(record.to_legacy())]

    def condition_monitoring_x_axis_label(self) -> str:
        indices = self.condition_monitoring_filtered_indices()
        if not indices:
            return "Arranque"
        dated = [self.records[index].timestamp_dt for index in indices]
        return "Mes" if all(dt is not None for dt in dated) else "Arranque"

    def condition_monitoring_x_tick_labels(self) -> List[str]:
        indices = self.condition_monitoring_filtered_indices()
        if not indices:
            return []
        dated = [self.records[index].timestamp_dt for index in indices]
        if not all(dt is not None for dt in dated):
            return [f"A{index + 1}" for index in indices]

        month_names = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        labels: List[str] = []
        last_month_key = None
        last_year = None
        for index in indices:
            dt = self.records[index].timestamp_dt
            month_key = (dt.year, dt.month)
            if month_key != last_month_key:
                month_label = month_names[dt.month - 1]
                if last_year is None or dt.year != last_year:
                    month_label = f"{month_label}\n{dt.year}"
                labels.append(month_label)
                last_month_key = month_key
                last_year = dt.year
            else:
                labels.append("")
        return labels

    def add_cm_metric(self, target: str, metric_name: str):
        metrics = self.cm_main_metrics if target == "main" else self.cm_secondary_metrics
        if metric_name in metrics or len(metrics) >= 4:
            return
        metrics.append(metric_name)

    def remove_cm_metric(self, target: str, metric_name: str):
        metrics = self.cm_main_metrics if target == "main" else self.cm_secondary_metrics
        if metric_name not in metrics or len(metrics) <= 1:
            return
        metrics.remove(metric_name)

    def cm_axis_label(self, metrics: List[str]) -> str:
        if not metrics:
            return "Valor"
        return metrics[0] if len(metrics) == 1 else "Valor"

    def cm_title(self, metrics: List[str], fallback: str) -> str:
        if not metrics:
            return fallback
        if len(metrics) == 1:
            return metrics[0]
        if len(metrics) == 2:
            return f"{metrics[0]} + {metrics[1]}"
        return f"{metrics[0]} + {metrics[1]} + {len(metrics) - 2} mas"

    def historical_payload(self) -> dict:
        legacy_records = [record.to_legacy() for record in self.records]
        metrics = compute_history_metrics(legacy_records)

        load_points = []
        omitted_load = 0
        for index, load_pct in enumerate(metrics["load_pct"]):
            try:
                numeric = float(load_pct)
            except Exception:
                numeric = np.nan
            if np.isnan(numeric):
                omitted_load += 1
                continue
            load_points.append((float(index + 1), numeric))

        success_count = sum(1 for flag in metrics["success_flags"] if flag)
        failure_count = sum(1 for flag in metrics["success_flags"] if not flag)
        success_ratios = self._counts_with_percentages(
            {"Exitosos": success_count, "Fallidos": failure_count}
        )

        cascade_counts = {"< 60": 0, "60 - 70": 0, "70 - 80": 0, "> 80": 0}
        omitted_cascade = 0
        for value in metrics["cascadeo"]:
            numeric = _safe_float(value)
            if np.isnan(numeric):
                omitted_cascade += 1
                continue
            if numeric < 60:
                cascade_counts["< 60"] += 1
            elif numeric <= 70:
                cascade_counts["60 - 70"] += 1
            elif numeric <= 80:
                cascade_counts["70 - 80"] += 1
            else:
                cascade_counts["> 80"] += 1

        current_counts = {"90 - 120": 0, "80 - 90 / 120 - 130": 0, "< 80 / > 130": 0}
        omitted_current = 0
        for value in metrics["current_pct_nominal"]:
            numeric = _safe_float(value)
            if np.isnan(numeric):
                omitted_current += 1
                continue
            if 90 <= numeric <= 120:
                current_counts["90 - 120"] += 1
            elif 80 <= numeric < 90 or 120 < numeric <= 130:
                current_counts["80 - 90 / 120 - 130"] += 1
            else:
                current_counts["< 80 / > 130"] += 1

        nominal_current = estimated_nominal_current(legacy_records)
        return {
            "load_points": load_points,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_ratios": success_ratios,
            "cascade_counts": cascade_counts,
            "cascade_ratios": self._counts_with_percentages(cascade_counts),
            "current_counts": current_counts,
            "current_ratios": self._counts_with_percentages(current_counts),
            "omitted_load": omitted_load,
            "omitted_cascade": omitted_cascade,
            "omitted_current": omitted_current,
            "nominal_current": nominal_current,
            "linearity_pairs": linearity_pairs(legacy_records, ["Ratio R", "resRatio"], ["Vel fin", "finalSpeed(rpm)"]),
            "current_analysis_pairs": successful_current_analysis_pairs(legacy_records, nominal_current),
            "speed_ratio_pairs": successful_speed_resistance_ratio_pairs(legacy_records, 1000.0),
        }

    def _counts_with_percentages(self, values: dict[str, int]) -> dict[str, float]:
        total = max(1, sum(max(0, int(value)) for value in values.values()))
        return {key: (100.0 * max(0, int(value)) / total) for key, value in values.items()}


def _safe_float(value) -> float:
    try:
        numeric = float(value)
    except Exception:
        return np.nan
    return numeric


def _format_scalar(value, unit: str = "") -> str:
    numeric = _safe_float(value)
    if np.isnan(numeric):
        return "N/D"
    suffix = f" {unit}" if unit else ""
    return f"{numeric:.1f}{suffix}"
