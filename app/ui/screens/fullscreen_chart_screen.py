from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.screen import MDScreen

from ..widgets.charts import MultiSeriesChart


class FullscreenChartScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "fullscreen_chart"

        root = MDBoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        self.controls = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
        self.reset_button = MDFlatButton(text="Reset", on_release=lambda *_: self.chart.reset_zoom())
        self.delete_button = MDFlatButton(text="Excluir puntos", on_release=lambda *_: self._toggle_delete_mode())
        self.restore_button = MDFlatButton(text="Restaurar", on_release=lambda *_: self.chart.restore_points())
        self.close_button = MDRaisedButton(text="Cerrar", on_release=lambda *_: self.app_controller.close_fullscreen_chart())
        for widget in (self.reset_button, self.delete_button, self.restore_button, self.close_button):
            self.controls.add_widget(widget)
        root.add_widget(self.controls)

        self.chart = MultiSeriesChart(size_hint=(1, 1))
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
        footer: str = "",
    ):
        self.chart.series = list(series)
        self.chart.x_axis_label = x_axis_label
        self.chart.y_axis_label = y_axis_label
        self.chart.chart_mode = chart_mode
        self.chart.show_legend = show_legend
        self.chart.show_points = show_points
        self.chart.open_fullscreen_callback = None
        self.chart.delete_mode = False
        self.delete_button.text = "Excluir puntos"
        self.chart.reset_zoom()
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        landscape = self.width > self.height and self.width > dp(700)
        self.chart.stroke_width = 2.2 if landscape else 1.8
