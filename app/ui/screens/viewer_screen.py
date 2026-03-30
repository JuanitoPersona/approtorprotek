from __future__ import annotations

import numpy as np
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen

from ...metrics import scalar_value
from ..widgets.cards import MetricCard, SectionCard
from ..widgets.charts import MultiSeriesChart


class ViewerScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "viewer"
        self.start_menu = None

        root = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        scroll = ScrollView(do_scroll_x=False)
        self.content = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(12),
            padding=(0, dp(4), 0, dp(24)),
        )
        scroll.add_widget(self.content)
        root.add_widget(scroll)
        self.add_widget(root)

        self.header_card = SectionCard("Visualizacion de Arranque")
        self.header_title = MDLabel(text="Visualizacion de Arranque", bold=True, font_style="H5", adaptive_height=True)
        self.header_subtitle = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.header_meta = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(10), row_default_height=dp(64), row_force_default=True)
        self.header_card.body.add_widget(self.header_title)
        self.header_card.body.add_widget(self.header_subtitle)
        self.header_card.body.add_widget(self.header_meta)
        self.content.add_widget(self.header_card)

        self.selector_card = SectionCard("Arranque activo")
        self.selector_button = MDRaisedButton(text="Seleccionar arranque", on_release=self._open_start_menu)
        self.selector_hint = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.selector_card.body.add_widget(self.selector_button)
        self.selector_card.body.add_widget(self.selector_hint)
        self.content.add_widget(self.selector_card)

        self.metrics_card = SectionCard("Resumen rapido")
        self.metrics_grid = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(10), row_default_height=dp(96), row_force_default=True)
        self.metrics_card.body.add_widget(self.metrics_grid)
        self.content.add_widget(self.metrics_card)

        self.secondary_metrics_card = SectionCard("Metrica tecnica")
        self.secondary_metrics_grid = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(10), row_default_height=dp(96), row_force_default=True)
        self.secondary_metrics_card.body.add_widget(self.secondary_metrics_grid)
        self.content.add_widget(self.secondary_metrics_card)

        self.detail_card = SectionCard("Detalle del arranque")
        self.detail_layout = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(8))
        self.detail_card.body.add_widget(self.detail_layout)
        self.content.add_widget(self.detail_card)

        self.signals_card = SectionCard("Senales principales")
        self.signal_chart = MultiSeriesChart(size_hint_y=None, height=dp(240))
        self.signals_card.body.add_widget(self.signal_chart)
        self.signals_card.body.add_widget(
            MDLabel(
                text="Velocidad, corriente y par apilados en una unica lectura temporal.",
                adaptive_height=True,
                theme_text_color="Secondary",
            )
        )
        self.content.add_widget(self.signals_card)

        self.torque_card = SectionCard("Par y carga")
        self.torque_chart = MultiSeriesChart(size_hint_y=None, height=dp(220))
        self.torque_card.body.add_widget(self.torque_chart)
        self.torque_card.body.add_widget(
            MDLabel(
                text="Relacion angular entre par resistente, par motor y referencia congelada.",
                adaptive_height=True,
                theme_text_color="Secondary",
            )
        )
        self.content.add_widget(self.torque_card)

        self.harmonics_card = SectionCard("Armonicos")
        self.harmonics_chart = MultiSeriesChart(size_hint_y=None, height=dp(180))
        self.harmonics_info = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.harmonics_card.body.add_widget(self.harmonics_chart)
        self.harmonics_card.body.add_widget(self.harmonics_info)
        self.content.add_widget(self.harmonics_card)

    def _open_start_menu(self, *_args):
        labels = self.app_controller.state.startup_labels()
        if len(labels) <= 1:
            return
        if self.start_menu:
            self.start_menu.dismiss()
        items = [
            {
                "text": label,
                "viewclass": "OneLineListItem",
                "on_release": lambda idx=index: self._select_startup(idx),
            }
            for index, label in enumerate(labels)
        ]
        self.start_menu = MDDropdownMenu(caller=self.selector_button, items=items, width_mult=4)
        self.start_menu.open()

    def _select_startup(self, index: int):
        self.app_controller.state.selected_start_index = index
        if self.start_menu:
            self.start_menu.dismiss()
        self.app_controller.refresh_ui()

    def refresh(self):
        state = self.app_controller.state
        record = state.current_record()
        if record is None:
            self._clear_view()
            return

        self._refresh_header(record)
        self._refresh_selector()
        self._refresh_metrics(record)
        self._refresh_detail(record)
        self._refresh_charts(record)

    def _clear_view(self):
        self.header_subtitle.text = "Carga un CSV para inspeccionar un arranque."
        self.selector_button.text = "Sin arranque"
        self.selector_button.disabled = True
        self.selector_hint.text = "La vista se activara cuando exista un dataset valido."
        self.metrics_grid.clear_widgets()
        self.secondary_metrics_grid.clear_widgets()
        self.detail_layout.clear_widgets()
        self.signal_chart.series = []
        self.torque_chart.series = []
        self.harmonics_chart.series = []
        self.harmonics_info.text = ""

    def _refresh_header(self, record):
        payload = self.app_controller.state.viewer_header_payload(record)
        self.header_title.text = payload["title"]
        self.header_subtitle.text = payload["subtitle"]
        self.header_meta.clear_widgets()
        for title, value in (
            ("Estado", payload["selection_text"]),
            ("Origen", payload["dataset_text"]),
        ):
            self.header_meta.add_widget(MetricCard(title, value))

    def _refresh_selector(self):
        labels = self.app_controller.state.startup_labels()
        index = self.app_controller.state.current_record_index()
        multi = len(labels) > 1
        self.selector_card.opacity = 1 if multi else 0
        self.selector_card.disabled = not multi
        self.selector_button.disabled = not multi
        if not labels:
            self.selector_button.text = "Sin arranque"
            self.selector_hint.text = ""
            return
        self.selector_button.text = labels[index]
        self.selector_hint.text = (
            "Selecciona el arranque activo que quieres inspeccionar en detalle."
            if multi
            else "El CSV contiene un unico arranque, asi que esta vista queda fijada automaticamente."
        )

    def _refresh_metrics(self, record):
        self.metrics_grid.clear_widgets()
        for title, value in self.app_controller.state.viewer_metric_cards(record):
            self.metrics_grid.add_widget(MetricCard(title, value))

        self.secondary_metrics_grid.clear_widgets()
        for title, value in self.app_controller.state.viewer_secondary_metrics(record):
            self.secondary_metrics_grid.add_widget(MetricCard(title, value))

    def _refresh_detail(self, record):
        self.detail_layout.clear_widgets()
        for label, value in self.app_controller.state.viewer_detail_rows(record):
            row = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(2))
            row.add_widget(MDLabel(text=label, adaptive_height=True, theme_text_color="Secondary"))
            row.add_widget(MDLabel(text=str(value), adaptive_height=True))
            self.detail_layout.add_widget(row)

    def _refresh_charts(self, record):
        time_axis = np.asarray(record.series.time, dtype=float)
        if time_axis.size == 0:
            size = max(len(record.series.speed), len(record.series.current), len(record.series.torque))
            time_axis = np.arange(size, dtype=float)
        self.signal_chart.series = [
            {"name": "Velocidad", "color": "#111111", "points": _points(time_axis, record.series.speed)},
            {"name": "Corriente", "color": "#EC6E00", "points": _points(time_axis, record.series.current)},
            {"name": "Par", "color": "#2E7D32", "points": _points(time_axis, record.series.torque)},
        ]

        load_torque = np.asarray(record.series.load_torque, dtype=float)
        motor_torque = np.asarray(record.series.motor_torque, dtype=float)
        angle_axis = np.linspace(0.0, 180.0, load_torque.size) if load_torque.size else np.array([])
        frozen_amp = scalar_value(record.to_legacy(), "Amp frz(%)")
        frozen_numeric = _safe_float(frozen_amp)
        frozen_curve = frozen_numeric * np.sin(np.radians(angle_axis)) if angle_axis.size and not np.isnan(frozen_numeric) else np.array([])
        self.torque_chart.series = [
            {"name": "Carga", "color": "#111111", "points": _points(angle_axis, load_torque)},
            {"name": "Motor", "color": "#EC6E00", "points": _points(angle_axis, motor_torque)},
            {"name": "Congelado", "color": "#1976D2", "points": _points(angle_axis, frozen_curve)},
        ]

        harmonic_points = _points(record.series.harmonic_freq_hz, record.series.harmonic_amp)
        self.harmonics_chart.series = [{"name": "Armonicos", "color": "#2E7D32", "points": harmonic_points}]
        self.harmonics_info.text = (
            f"{len(harmonic_points)} armonicos validos detectados."
            if harmonic_points
            else "Este arranque no aporta armonicos validos para representar."
        )


def _points(xs, ys):
    values = []
    for x_value, y_value in zip(np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)):
        if np.isnan(x_value) or np.isnan(y_value):
            continue
        values.append((float(x_value), float(y_value)))
    return values


def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return np.nan
