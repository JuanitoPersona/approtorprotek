from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from ..widgets.charts import MultiSeriesChart


class FullscreenChartScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "fullscreen_chart"

        root = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        header = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6))
        self.title_label = MDLabel(text="Grafica", bold=True, font_style="H5", adaptive_height=True)
        self.subtitle_label = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        header.add_widget(self.title_label)
        header.add_widget(self.subtitle_label)
        root.add_widget(header)

        controls = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
        controls.add_widget(MDFlatButton(text="Zoom -", on_release=lambda *_: self.chart.zoom_out()))
        controls.add_widget(MDFlatButton(text="Reset", on_release=lambda *_: self.chart.reset_zoom()))
        controls.add_widget(MDFlatButton(text="Zoom +", on_release=lambda *_: self.chart.zoom_in()))
        controls.add_widget(MDRaisedButton(text="Cerrar", on_release=lambda *_: self.app_controller.close_fullscreen_chart()))
        root.add_widget(controls)

        self.chart = MultiSeriesChart(size_hint=(1, 1))
        root.add_widget(self.chart)

        self.footer_label = MDLabel(
            text="Pinza para zoom, arrastra para navegar y doble toque para recentrar.",
            adaptive_height=True,
            theme_text_color="Secondary",
        )
        root.add_widget(self.footer_label)
        self.add_widget(root)
        self.bind(size=lambda *_: self._apply_responsive_layout())
        self._apply_responsive_layout()

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
        self.title_label.text = title
        self.subtitle_label.text = subtitle
        self.chart.series = list(series)
        self.chart.x_axis_label = x_axis_label
        self.chart.y_axis_label = y_axis_label
        self.chart.chart_mode = chart_mode
        self.chart.show_legend = show_legend
        self.chart.show_points = show_points
        self.chart.open_fullscreen_callback = None
        self.chart.reset_zoom()
        self.footer_label.text = footer or "Pinza para zoom, arrastra para navegar y usa Reset para volver al encuadre inicial."
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        landscape = self.width > self.height and self.width > dp(700)
        self.chart.stroke_width = 2.2 if landscape else 1.8
