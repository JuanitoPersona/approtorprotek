from __future__ import annotations

import numpy as np
from kivy.effects.scroll import ScrollEffect
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
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
        scroll = ScrollView(do_scroll_x=False, effect_cls=ScrollEffect)
        self.scroll = scroll
        self.scroll.bind(scroll_y=lambda *_args: self.app_controller.handle_screen_scroll(self.scroll.scroll_y))
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
        self.harmonics_toggle_button = MDFlatButton(text="Ocultar armonicos", on_release=self._toggle_harmonics)
        self.selector_hint = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.selector_card.body.add_widget(self.selector_button)
        self.selector_card.body.add_widget(self.harmonics_toggle_button)
        self.selector_card.body.add_widget(self.selector_hint)
        self.content.add_widget(self.selector_card)

        self.analysis_grid = MDGridLayout(cols=1, adaptive_height=True, spacing=dp(12))
        self.content.add_widget(self.analysis_grid)

        self.metrics_card = SectionCard("Resumen rapido")
        self.metrics_grid = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(10), row_default_height=dp(96), row_force_default=True)
        self.metrics_card.body.add_widget(self.metrics_grid)
        self.analysis_grid.add_widget(self.metrics_card)

        self.secondary_metrics_card = SectionCard("Metrica tecnica")
        self.secondary_metrics_grid = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(10), row_default_height=dp(96), row_force_default=True)
        self.secondary_metrics_card.body.add_widget(self.secondary_metrics_grid)
        self.analysis_grid.add_widget(self.secondary_metrics_card)

        self.detail_card = SectionCard("Detalle del arranque")
        self.detail_layout = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(8))
        self.detail_card.body.add_widget(self.detail_layout)
        self.analysis_grid.add_widget(self.detail_card)

        self.signals_card = SectionCard("Senales principales")
        self.signal_chart = MultiSeriesChart(size_hint_y=None, height=dp(240), x_axis_label="Tiempo [s]", y_axis_label="% nominal")
        self.signal_chart.max_points = 1400
        self.signal_chart.open_fullscreen_callback = self._open_signal_chart_fullscreen
        self.signals_card.body.add_widget(_chart_controls(self.app_controller, self.signal_chart, self._open_signal_chart_fullscreen))
        self.signals_card.body.add_widget(self.signal_chart)
        self.signals_help_label = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.signals_card.body.add_widget(self.signals_help_label)
        self.content.add_widget(self.signals_card)

        self.torque_card = SectionCard("Par y carga")
        self.torque_chart = MultiSeriesChart(size_hint_y=None, height=dp(220), x_axis_label="Angulo [deg]", y_axis_label="% nominal")
        self.torque_chart.max_points = 1000
        self.torque_chart.open_fullscreen_callback = self._open_torque_chart_fullscreen
        self.torque_card.body.add_widget(_chart_controls(self.app_controller, self.torque_chart, self._open_torque_chart_fullscreen))
        self.torque_card.body.add_widget(self.torque_chart)
        self.torque_help_label = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.torque_card.body.add_widget(self.torque_help_label)
        self.content.add_widget(self.torque_card)

        self.params_table_card = SectionCard("Tabla de parametros")
        self.params_table_grid = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(8))
        self.params_table_card.body.add_widget(self.params_table_grid)
        self.content.add_widget(self.params_table_card)

        self.harmonics_card = SectionCard("Armonicos")
        self.harmonics_chart = MultiSeriesChart(
            size_hint_y=None,
            height=dp(220),
            x_axis_label="Frecuencia [Hz]",
            y_axis_label="% Imax",
            chart_mode="bar",
            show_legend=False,
        )
        self.harmonics_chart.max_points = 256
        self.harmonics_chart.open_fullscreen_callback = self._open_harmonics_chart_fullscreen
        self.harmonics_card.body.add_widget(_chart_controls(self.app_controller, self.harmonics_chart, self._open_harmonics_chart_fullscreen))
        self.harmonics_info = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.harmonics_card.body.add_widget(self.harmonics_chart)
        self.harmonics_card.body.add_widget(self.harmonics_info)
        self.content.add_widget(self.harmonics_card)
        self.bind(size=lambda *_: self._apply_responsive_layout())
        self._apply_responsive_layout()

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

    def _toggle_harmonics(self, *_args):
        self.app_controller.state.show_harmonics = not self.app_controller.state.show_harmonics
        self.refresh()

    def _open_signal_chart_fullscreen(self, *_args):
        self.app_controller.open_fullscreen_chart(
            title="Senales principales",
            subtitle="Vista ampliada del arranque activo.",
            series=list(self.signal_chart.series),
            x_axis_label=self.signal_chart.x_axis_label,
            y_axis_label=self.signal_chart.y_axis_label,
            chart_mode=self.signal_chart.chart_mode,
            show_legend=self.signal_chart.show_legend,
            show_points=self.signal_chart.show_points,
            x_tick_labels=list(self.signal_chart.x_tick_labels),
            footer=self.app_controller.tr("viewer_signals_footer"),
        )

    def _open_torque_chart_fullscreen(self, *_args):
        self.app_controller.open_fullscreen_chart(
            title="Par y carga",
            subtitle="Vista ampliada de la relacion angular del arranque.",
            series=list(self.torque_chart.series),
            x_axis_label=self.torque_chart.x_axis_label,
            y_axis_label=self.torque_chart.y_axis_label,
            chart_mode=self.torque_chart.chart_mode,
            show_legend=self.torque_chart.show_legend,
            show_points=self.torque_chart.show_points,
            x_tick_labels=list(self.torque_chart.x_tick_labels),
            footer=self.app_controller.tr("viewer_torque_footer"),
        )

    def _open_harmonics_chart_fullscreen(self, *_args):
        self.app_controller.open_fullscreen_chart(
            title="Armonicos",
            subtitle="Vista ampliada del espectro del arranque activo.",
            series=list(self.harmonics_chart.series),
            x_axis_label=self.harmonics_chart.x_axis_label,
            y_axis_label=self.harmonics_chart.y_axis_label,
            chart_mode=self.harmonics_chart.chart_mode,
            show_legend=self.harmonics_chart.show_legend,
            show_points=self.harmonics_chart.show_points,
            x_tick_labels=list(self.harmonics_chart.x_tick_labels),
            footer=self.app_controller.tr("viewer_harmonics_footer"),
        )

    def refresh(self):
        state = self.app_controller.state
        record = state.current_record()
        if record is None:
            self._clear_view()
            return

        self.header_card.title_label.text = self.app_controller.tr("viewer_title")
        self.selector_card.title_label.text = self.app_controller.tr("active_start")
        self.selector_button.text = self.app_controller.tr("select_start")
        self.metrics_card.title_label.text = self.app_controller.tr("quick_summary")
        self.secondary_metrics_card.title_label.text = self.app_controller.tr("technical_metric")
        self.detail_card.title_label.text = self.app_controller.tr("startup_detail")
        self.signals_card.title_label.text = self.app_controller.tr("main_signals")
        self.torque_card.title_label.text = self.app_controller.tr("torque_load")
        self.params_table_card.title_label.text = self.app_controller.tr("params_table")
        self.harmonics_card.title_label.text = self.app_controller.tr("harmonics")
        self.signals_help_label.text = self.app_controller.tr("viewer_signals_help")
        self.torque_help_label.text = self.app_controller.tr("viewer_torque_help")
        self._refresh_header(record)
        self._refresh_selector()
        self._refresh_metrics(record)
        self._refresh_detail(record)
        self._refresh_parameter_table(record)
        self._refresh_charts(record)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        landscape = self.width > self.height and self.width > dp(700)
        self.header_meta.cols = 2 if landscape else 1
        self.analysis_grid.cols = 2 if landscape else 1
        self.metrics_grid.cols = 4 if landscape else 2
        self.secondary_metrics_grid.cols = 4 if landscape else 2
        self.signal_chart.height = dp(300) if landscape else dp(240)
        self.torque_chart.height = dp(280) if landscape else dp(220)
        self.harmonics_chart.height = dp(280) if landscape else dp(240)

    def _clear_view(self):
        self.header_subtitle.text = self.app_controller.tr("viewer_empty_subtitle")
        self.header_card.title_label.text = self.app_controller.tr("viewer_title")
        self.selector_card.title_label.text = self.app_controller.tr("active_start")
        self.selector_button.text = self.app_controller.tr("summary_selection_none")
        self.selector_button.disabled = True
        self.selector_hint.text = self.app_controller.tr("viewer_empty_hint")
        self.metrics_grid.clear_widgets()
        self.secondary_metrics_grid.clear_widgets()
        self.detail_layout.clear_widgets()
        self.params_table_grid.clear_widgets()
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
            (self.app_controller.tr_metric("Estado"), payload["selection_text"]),
            (self.app_controller.tr_metric("Origen"), payload["dataset_text"]),
        ):
            self.header_meta.add_widget(MetricCard(title, value))

    def _refresh_selector(self):
        labels = self.app_controller.state.startup_labels()
        index = self.app_controller.state.current_record_index()
        multi = len(labels) > 1
        self.selector_card.opacity = 1 if multi else 0
        self.selector_card.disabled = not multi
        self.selector_card.height = self.selector_card.minimum_height if multi else 0
        self.selector_button.disabled = not multi
        if not labels:
            self.selector_button.text = self.app_controller.tr("summary_selection_none")
            self.selector_hint.text = ""
            return
        self.selector_button.text = labels[index]
        self.harmonics_toggle_button.text = self.app_controller.tr("show_harmonics") if not self.app_controller.state.show_harmonics else self.app_controller.tr("hide_harmonics")
        self.selector_hint.text = (
            self.app_controller.tr("viewer_select_hint_multi")
            if multi
            else self.app_controller.tr("viewer_select_hint_single")
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
            row.add_widget(MDLabel(text=self.app_controller.tr_metric(label), adaptive_height=True, theme_text_color="Secondary"))
            row.add_widget(MDLabel(text=str(value), adaptive_height=True))
            self.detail_layout.add_widget(row)

    def _refresh_parameter_table(self, record):
        self.params_table_grid.clear_widgets()
        for label, value in self.app_controller.state.viewer_parameter_rows(record):
            self.params_table_grid.add_widget(MDLabel(text=self.app_controller.tr_metric(str(label)), adaptive_height=True, theme_text_color="Secondary"))
            self.params_table_grid.add_widget(MDLabel(text=str(value), adaptive_height=True))

    def _refresh_charts(self, record):
        time_axis = np.asarray(record.series.time, dtype=float)
        if time_axis.size == 0:
            size = max(len(record.series.speed), len(record.series.current), len(record.series.torque))
            time_axis = np.arange(size, dtype=float)
        self.signal_chart.series = [
            {"name": self.app_controller.tr_metric("Velocidad"), "color": "#111111", "points": _points(time_axis, record.series.speed)},
            {"name": self.app_controller.tr_metric("Corriente"), "color": "#EC6E00", "points": _points(time_axis, record.series.current)},
            {"name": self.app_controller.tr_metric("Par"), "color": "#2E7D32", "points": _points(time_axis, record.series.torque)},
        ]
        dual_points = _points(time_axis[: len(record.series.dual_current)], record.series.dual_current)
        if dual_points:
            self.signal_chart.series.append({"name": self.app_controller.tr_metric("Corriente 2 motor"), "color": "#1976D2", "points": dual_points})

        load_torque, motor_torque, angle_axis = _torque_load_geometry(record)
        frozen_amp = scalar_value(record.to_legacy(), "Amp frz(%)")
        frozen_numeric = _safe_float(frozen_amp)
        frozen_curve = frozen_numeric * np.sin(np.radians(angle_axis)) if angle_axis.size and not np.isnan(frozen_numeric) else np.array([])
        self.torque_chart.series = [
            {"name": self.app_controller.tr_metric("Carga"), "color": "#111111", "points": _points(angle_axis, load_torque)},
            {"name": self.app_controller.tr_metric("Motor"), "color": "#EC6E00", "points": _points(angle_axis, motor_torque)},
            {"name": self.app_controller.tr_metric("Congelado"), "color": "#1976D2", "points": _points(angle_axis, frozen_curve)},
        ]

        max_current = _safe_float(record.scalars.get("I m\xE1x (Arms)"))
        harmonic_amp = np.asarray(record.series.harmonic_amp, dtype=float)
        if not np.isnan(max_current) and max_current > 0:
            harmonic_amp = harmonic_amp / max_current * 100.0
        harmonic_points = [
            point
            for point in _points(record.series.harmonic_freq_hz, harmonic_amp)
            if point[0] > 0 and point[1] > 0
        ]
        visible = self.app_controller.state.show_harmonics
        self.harmonics_card.opacity = 1 if visible else 0
        self.harmonics_card.disabled = not visible
        self.harmonics_card.height = self.harmonics_card.minimum_height if visible else 0
        self.harmonics_chart.series = [{"name": self.app_controller.tr_metric("Armonicos"), "color": "#2E7D32", "points": harmonic_points}] if visible else []
        self.harmonics_info.text = (
            self.app_controller.tr("harmonics_info_count", count=len(harmonic_points))
            if visible and harmonic_points
            else (self.app_controller.tr("harmonics_info_none") if visible else self.app_controller.tr("harmonics_info_hidden"))
        )

    def apply_theme(self, palette: dict):
        self.md_bg_color = palette["background"]
        self.header_title.theme_text_color = "Custom"
        self.header_title.text_color = palette["text"]
        for label in (
            self.header_subtitle,
            self.selector_hint,
            self.signals_help_label,
            self.torque_help_label,
            self.harmonics_info,
        ):
            label.theme_text_color = "Custom"
            label.text_color = palette["subtext"]
        for child in self.detail_layout.children:
            for subchild in child.children:
                if hasattr(subchild, "theme_text_color"):
                    subchild.theme_text_color = "Custom"
                    subchild.text_color = palette["text"]
        for child in self.params_table_grid.children:
            if hasattr(child, "theme_text_color"):
                child.theme_text_color = "Custom"
                child.text_color = palette["text"]


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


def _torque_load_geometry(record):
    load_torque = np.asarray(record.series.load_torque, dtype=float)
    motor_torque = np.asarray(record.series.motor_torque, dtype=float)

    if load_torque.size == 0 and motor_torque.size == 0:
        return load_torque, motor_torque, np.array([], dtype=float)

    last_finite_index = -1
    for array in (load_torque, motor_torque):
        finite_indices = np.where(np.isfinite(array))[0]
        if finite_indices.size:
            last_finite_index = max(last_finite_index, int(finite_indices[-1]))

    if last_finite_index >= 0:
        end = last_finite_index + 1
        load_torque = load_torque[:end]
        motor_torque = motor_torque[:end]

    point_count = max(load_torque.size, motor_torque.size)
    angle_axis = np.linspace(0.0, 180.0, point_count) if point_count else np.array([], dtype=float)
    return load_torque, motor_torque, angle_axis


def _chart_controls(app_controller, chart, fullscreen_callback):
    row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
    row.add_widget(MDFlatButton(text=app_controller.tr("reset"), on_release=lambda *_: chart.reset_zoom()))
    row.add_widget(MDRaisedButton(text=app_controller.tr("fullscreen"), on_release=fullscreen_callback))
    return row
