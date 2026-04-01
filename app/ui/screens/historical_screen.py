from __future__ import annotations

from kivy.effects.scroll import ScrollEffect
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
        self.page_title = MDLabel(text="Historico", bold=True, font_style="H5", adaptive_height=True)
        self.page_subtitle = MDLabel(text="Tendencias historicas y clasificacion operativa.", theme_text_color="Secondary", adaptive_height=True)
        root.add_widget(self.page_title)
        root.add_widget(self.page_subtitle)

        scroll = ScrollView(do_scroll_x=False, effect_cls=ScrollEffect)
        self.scroll = scroll
        self.scroll.bind(scroll_y=lambda *_args: self.app_controller.handle_screen_scroll(self.scroll.scroll_y))
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
        self.load_axis_info = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.load_card.body.add_widget(self.load_axis_info)
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
        self.bind(size=lambda *_: self._apply_responsive_layout())
        self._apply_responsive_layout()

    def _build_pie_card(self, title: str):
        card = SectionCard(title)
        chart = PieChartWidget(size_hint_y=None, height=dp(280))
        info = MDLabel(adaptive_height=True, theme_text_color="Secondary")
        card.body.add_widget(chart)
        card.body.add_widget(info)
        return card, chart, info

    def _open_load_chart_fullscreen(self, *_args):
        self.app_controller.open_fullscreen_chart(
            title=self.app_controller.tr("history_fullscreen_title"),
            subtitle=self.app_controller.tr("history_fullscreen_subtitle"),
            series=list(self.load_chart.series),
            x_axis_label=self.load_chart.x_axis_label,
            y_axis_label=self.load_chart.y_axis_label,
            chart_mode=self.load_chart.chart_mode,
            show_legend=self.load_chart.show_legend,
            show_points=self.load_chart.show_points,
            footer=self.app_controller.tr("history_fullscreen_footer"),
        )

    def refresh(self):
        state = self.app_controller.state
        self.page_title.text = self.app_controller.tr("history_title")
        self.page_subtitle.text = self.app_controller.tr("history_subtitle")
        self.load_card.title_label.text = self.app_controller.tr("history_load")
        self.load_axis_info.text = self.app_controller.tr("history_load_axes")
        self.success_card.title_label.text = self.app_controller.tr("history_success")
        self.cascade_card.title_label.text = self.app_controller.tr("history_cascade")
        self.current_card.title_label.text = self.app_controller.tr("history_current")
        self.empty_state.text_widget.text = self.app_controller.tr("history_empty")
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
        self.load_chart.series = [{"name": self.app_controller.tr_metric("Carga"), "color": "#EC6E00", "points": payload["load_points"]}]
        self.load_info.text = (
            self.app_controller.tr("history_load_info_omitted", count=payload["omitted_load"])
            if payload["omitted_load"]
            else self.app_controller.tr("history_load_info_none")
        )

        self.success_chart.segments = [
            {"label": self.app_controller.tr_metric("Exitosos"), "value": payload["success_count"], "color": "#2E7D32"},
            {"label": self.app_controller.tr_metric("Fallidos"), "value": payload["failure_count"], "color": "#C62828"},
        ]
        self.success_info.text = self.app_controller.tr(
            "history_success_info",
            success=payload["success_count"],
            success_pct=payload["success_ratios"]["Exitosos"],
            failure=payload["failure_count"],
            failure_pct=payload["success_ratios"]["Fallidos"],
        )

        self.cascade_chart.segments = [
            {"label": "< 60", "value": payload["cascade_counts"]["< 60"], "color": "#2E7D32"},
            {"label": "60 - 70", "value": payload["cascade_counts"]["60 - 70"], "color": "#F9A825"},
            {"label": "70 - 80", "value": payload["cascade_counts"]["70 - 80"], "color": "#EF6C00"},
            {"label": "> 80", "value": payload["cascade_counts"]["> 80"], "color": "#C62828"},
        ]
        self.cascade_info.text = self.app_controller.tr(
            "history_cascade_info",
            low=payload["cascade_ratios"]["< 60"],
            mid1=payload["cascade_ratios"]["60 - 70"],
            mid2=payload["cascade_ratios"]["70 - 80"],
            high=payload["cascade_ratios"]["> 80"],
            omitted=payload["omitted_cascade"],
        )

        self.current_chart.segments = [
            {"label": "90 - 120", "value": payload["current_counts"]["90 - 120"], "color": "#2E7D32"},
            {"label": "80 - 90 / 120 - 130", "value": payload["current_counts"]["80 - 90 / 120 - 130"], "color": "#EF6C00"},
            {"label": "< 80 / > 130", "value": payload["current_counts"]["< 80 / > 130"], "color": "#C62828"},
        ]
        self.current_info.text = self.app_controller.tr(
            "history_current_info",
            ok=payload["current_ratios"]["90 - 120"],
            warn=payload["current_ratios"]["80 - 90 / 120 - 130"],
            bad=payload["current_ratios"]["< 80 / > 130"],
            omitted=payload["omitted_current"],
        )
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        landscape = self.width > self.height and self.width > dp(700)
        self.pies_grid.cols = 3 if landscape else 1
        self.load_chart.height = dp(300) if landscape else dp(230)
        pie_height = dp(260) if landscape else dp(280)
        self.success_chart.height = pie_height
        self.cascade_chart.height = pie_height
        self.current_chart.height = pie_height


def _chart_controls(chart, fullscreen_callback):
    row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
    row.add_widget(MDFlatButton(text="Reset", on_release=lambda *_: chart.reset_zoom()))
    row.add_widget(MDRaisedButton(text="Pantalla completa", on_release=fullscreen_callback))
    return row
