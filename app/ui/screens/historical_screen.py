from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from ..widgets.cards import EmptyState, SectionCard
from ..widgets.charts import MultiSeriesChart, PieChartWidget


class HistoricalScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "historical"

        root = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        root.add_widget(MDLabel(text="Historico", bold=True, font_style="H5", adaptive_height=True))
        root.add_widget(MDLabel(text="Tendencias historicas y clasificacion operativa.", theme_text_color="Secondary", adaptive_height=True))

        scroll = ScrollView(do_scroll_x=False)
        self.content = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(12), padding=(0, dp(8), 0, dp(24)))
        scroll.add_widget(self.content)
        root.add_widget(scroll)
        self.add_widget(root)

        self.load_card = SectionCard("Evolucion historica del % de carga")
        self.load_chart = MultiSeriesChart(
            size_hint_y=None,
            height=dp(230),
            x_axis_label="Arranque",
            y_axis_label="% de carga",
            show_points=True,
        )
        self.load_chart.open_fullscreen_callback = self._open_load_chart_fullscreen
        self.load_card.body.add_widget(_chart_controls(self.load_chart, self._open_load_chart_fullscreen))
        self.load_info = MDLabel(adaptive_height=True, theme_text_color="Secondary")
        self.load_card.body.add_widget(self.load_chart)
        self.load_card.body.add_widget(MDLabel(text="Eje X: orden temporal de arranques | Eje Y: % de carga", adaptive_height=True, theme_text_color="Secondary"))
        self.load_card.body.add_widget(self.load_info)
        self.content.add_widget(self.load_card)

        self.pies_grid = MDGridLayout(cols=1, adaptive_height=True, spacing=dp(12))
        self.content.add_widget(self.pies_grid)
        self.success_card, self.success_chart, self.success_info = self._build_pie_card("Arranques exitosos y fallidos")
        self.cascade_card, self.cascade_chart, self.cascade_info = self._build_pie_card("Cascadeo")
        self.current_card, self.current_chart, self.current_info = self._build_pie_card("% de corriente nominal")
        self.pies_grid.add_widget(self.success_card)
        self.pies_grid.add_widget(self.cascade_card)
        self.pies_grid.add_widget(self.current_card)

        self.empty_state = EmptyState("Historico solo esta disponible cuando el CSV contiene multiples arranques.")
        self.content.add_widget(self.empty_state)

    def _build_pie_card(self, title: str):
        card = SectionCard(title)
        chart = PieChartWidget(size_hint_y=None, height=dp(220))
        info = MDLabel(adaptive_height=True, theme_text_color="Secondary")
        card.body.add_widget(chart)
        card.body.add_widget(info)
        return card, chart, info

    def _open_load_chart_fullscreen(self, *_args):
        self.app_controller.open_fullscreen_chart(
            title="Historico de carga",
            subtitle="Evolucion temporal del porcentaje de carga.",
            series=list(self.load_chart.series),
            x_axis_label=self.load_chart.x_axis_label,
            y_axis_label=self.load_chart.y_axis_label,
            chart_mode=self.load_chart.chart_mode,
            show_legend=self.load_chart.show_legend,
            show_points=self.load_chart.show_points,
            footer="En pantalla completa el gesto tactil no compite con el scroll del historico.",
        )

    def refresh(self):
        state = self.app_controller.state
        visible = state.is_multi
        for widget in (self.load_card, self.success_card, self.cascade_card, self.current_card):
            widget.opacity = 1 if visible else 0
            widget.disabled = not visible
        self.empty_state.opacity = 0 if visible else 1
        self.empty_state.disabled = visible
        if not visible:
            self.load_chart.series = []
            self.success_chart.segments = []
            self.cascade_chart.segments = []
            self.current_chart.segments = []
            return

        payload = state.historical_payload()
        self.load_chart.series = [{"name": "Carga", "color": "#EC6E00", "points": payload["load_points"]}]
        self.load_info.text = (
            f"Se omitieron {payload['omitted_load']} arranques sin % de carga calculable."
            if payload["omitted_load"]
            else "Todos los arranques validos aportan % de carga."
        )

        self.success_chart.segments = [
            {"label": "Exitosos", "value": payload["success_count"], "color": "#2E7D32"},
            {"label": "Fallidos", "value": payload["failure_count"], "color": "#C62828"},
        ]
        self.success_info.text = (
            f"Exitosos: {payload['success_count']} ({payload['success_ratios']['Exitosos']:.0f}%) | "
            f"Fallidos: {payload['failure_count']} ({payload['success_ratios']['Fallidos']:.0f}%)"
        )

        self.cascade_chart.segments = [
            {"label": "< 60", "value": payload["cascade_counts"]["< 60"], "color": "#2E7D32"},
            {"label": "60 - 70", "value": payload["cascade_counts"]["60 - 70"], "color": "#F9A825"},
            {"label": "70 - 80", "value": payload["cascade_counts"]["70 - 80"], "color": "#EF6C00"},
            {"label": "> 80", "value": payload["cascade_counts"]["> 80"], "color": "#C62828"},
        ]
        self.cascade_info.text = (
            "Clasificacion calculada desde Angulo (deg). "
            f"< 60: {payload['cascade_ratios']['< 60']:.0f}% | "
            f"60 - 70: {payload['cascade_ratios']['60 - 70']:.0f}% | "
            f"70 - 80: {payload['cascade_ratios']['70 - 80']:.0f}% | "
            f"> 80: {payload['cascade_ratios']['> 80']:.0f}%. "
            f"Omitidos: {payload['omitted_cascade']}."
        )

        self.current_chart.segments = [
            {"label": "90 - 120", "value": payload["current_counts"]["90 - 120"], "color": "#2E7D32"},
            {"label": "80 - 90 / 120 - 130", "value": payload["current_counts"]["80 - 90 / 120 - 130"], "color": "#EF6C00"},
            {"label": "< 80 / > 130", "value": payload["current_counts"]["< 80 / > 130"], "color": "#C62828"},
        ]
        self.current_info.text = (
            f"90 - 120: {payload['current_ratios']['90 - 120']:.0f}% | "
            f"80 - 90 / 120 - 130: {payload['current_ratios']['80 - 90 / 120 - 130']:.0f}% | "
            f"< 80 / > 130: {payload['current_ratios']['< 80 / > 130']:.0f}%. "
            f"Omitidos: {payload['omitted_current']}."
        )


def _chart_controls(chart, fullscreen_callback):
    row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
    row.add_widget(MDFlatButton(text="Zoom -", on_release=lambda *_: chart.zoom_out()))
    row.add_widget(MDFlatButton(text="Reset", on_release=lambda *_: chart.reset_zoom()))
    row.add_widget(MDFlatButton(text="Zoom +", on_release=lambda *_: chart.zoom_in()))
    row.add_widget(MDRaisedButton(text="Pantalla completa", on_release=fullscreen_callback))
    return row
