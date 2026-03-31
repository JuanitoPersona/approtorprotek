from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.screen import MDScreen

from ..widgets.charts import MultiSeriesChart


class FullscreenChartScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "fullscreen_chart"

        root = MDBoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        self.controls = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(8), row_default_height=dp(42), row_force_default=True)
        self.reset_button = MDFlatButton(text="Reset", on_release=lambda *_: self.chart.reset_zoom())
        self.delete_button = MDFlatButton(text="Excluir puntos", on_release=lambda *_: self._toggle_delete_mode())
        self.restore_button = MDFlatButton(text="Restaurar", on_release=lambda *_: self.chart.restore_points())
        self.close_button = MDRaisedButton(text="Cerrar", on_release=lambda *_: self.app_controller.close_fullscreen_chart())
        for widget in (self.reset_button, self.delete_button, self.restore_button, self.close_button):
            widget.size_hint_x = 1
            self.controls.add_widget(widget)
        root.add_widget(self.controls)

        self.chart = MultiSeriesChart(size_hint=(1, 1))
        self.chart.enable_touch_navigation = True
        root.add_widget(self.chart)
        self.add_widget(root)
        self.bind(size=lambda *_: self._apply_responsive_layout())
        self._apply_responsive_layout()

    def _toggle_delete_mode(self):
        self.chart.toggle_delete_mode()
        self.delete_button.text = "Salir excluir" if self.chart.delete_mode else "Excluir puntos"

    def apply_chart(
        self,
        *,
        title: str,
        subtitle: str,
        series: list[dict],
        x_axis_label: str,
        y_axis_label: str,
        chart_mode: str = "line",
        show_legend: bool = True,
        show_points: bool = False,
        x_tick_labels: list[str] | None = None,
        allow_point_deletion: bool = False,
        footer: str = "",
    ):
        self.chart.load_series_for_view(series)
        self.chart.x_axis_label = x_axis_label
        self.chart.y_axis_label = y_axis_label
        self.chart.chart_mode = chart_mode
        self.chart.show_legend = show_legend
        self.chart.show_points = show_points
        self.chart.x_tick_labels = list(x_tick_labels or [])
        self.chart.open_fullscreen_callback = None
        self.chart.enable_touch_navigation = True
        self.chart.allow_point_deletion = allow_point_deletion
        self.chart.delete_mode = False
        self.chart.clear_interaction_state()
        self.delete_button.text = "Excluir puntos"
        self.delete_button.disabled = not allow_point_deletion
        self.delete_button.opacity = 1 if allow_point_deletion else 0
        self.restore_button.disabled = not allow_point_deletion
        self.restore_button.opacity = 1 if allow_point_deletion else 0
        self.chart.reset_zoom()
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        landscape = self.width > self.height and self.width > dp(700)
        self.chart.stroke_width = 2.2 if landscape else 1.8
        self.controls.cols = 4 if landscape else 2
