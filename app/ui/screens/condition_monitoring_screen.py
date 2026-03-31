from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen

from ...models import SCALAR_FIELDS
from ..widgets.cards import EmptyState, SectionCard
from ..widgets.charts import MultiSeriesChart


class ConditionMonitoringScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "condition_monitoring"
        self.main_menu = None
        self.secondary_menu = None

        root = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        root.add_widget(MDLabel(text="Condition Monitoring", bold=True, font_style="H5", adaptive_height=True))
        root.add_widget(MDLabel(text="Comparativa compacta y movil.", theme_text_color="Secondary", adaptive_height=True))

        scroll = ScrollView(do_scroll_x=False)
        self.content = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(12), padding=(0, dp(8), 0, dp(24)))
        scroll.add_widget(self.content)
        root.add_widget(scroll)
        self.add_widget(root)

        self.selector_card = SectionCard("Variables")
        self.main_metric_button = MDRaisedButton(text="Metrica principal", on_release=self._open_main_metric_menu)
        self.secondary_metric_button = MDRaisedButton(text="Metrica secundaria", on_release=self._open_secondary_metric_menu)
        self.selector_card.body.add_widget(self.main_metric_button)
        self.selector_card.body.add_widget(self.secondary_metric_button)
        self.selector_card.body.add_widget(
            MDLabel(
                text="La pantalla reutiliza las metricas escalares del escritorio y las presenta en formato vertical para movil.",
                adaptive_height=True,
                theme_text_color="Secondary",
            )
        )
        self.content.add_widget(self.selector_card)

        self.main_chart_card = SectionCard("Serie principal")
        self.main_chart = MultiSeriesChart(size_hint_y=None, height=dp(220), x_axis_label="Arranque", y_axis_label="Valor", show_points=True)
        self.main_chart.open_fullscreen_callback = self._open_main_chart_fullscreen
        self.main_chart_card.body.add_widget(_chart_controls(self.main_chart, self._open_main_chart_fullscreen))
        self.main_warning = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.main_chart_card.body.add_widget(self.main_chart)
        self.main_chart_card.body.add_widget(self.main_warning)
        self.content.add_widget(self.main_chart_card)

        self.secondary_chart_card = SectionCard("Serie secundaria")
        self.secondary_chart = MultiSeriesChart(size_hint_y=None, height=dp(220), x_axis_label="Arranque", y_axis_label="Valor", show_points=True)
        self.secondary_chart.open_fullscreen_callback = self._open_secondary_chart_fullscreen
        self.secondary_chart_card.body.add_widget(_chart_controls(self.secondary_chart, self._open_secondary_chart_fullscreen))
        self.secondary_warning = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.secondary_chart_card.body.add_widget(self.secondary_chart)
        self.secondary_chart_card.body.add_widget(self.secondary_warning)
        self.content.add_widget(self.secondary_chart_card)

        self.empty_state = EmptyState("Condition Monitoring solo esta disponible si el CSV contiene multiples arranques.")
        self.content.add_widget(self.empty_state)

    def _open_main_metric_menu(self, *_args):
        self.main_menu = self._build_metric_menu(self.main_metric_button, "main")
        self.main_menu.open()

    def _open_secondary_metric_menu(self, *_args):
        self.secondary_menu = self._build_metric_menu(self.secondary_metric_button, "secondary")
        self.secondary_menu.open()

    def _build_metric_menu(self, caller, target: str):
        items = [
            {
                "text": metric_name,
                "viewclass": "OneLineListItem",
                "on_release": lambda name=metric_name, side=target: self._select_metric(side, name),
            }
            for metric_name in SCALAR_FIELDS
        ]
        return MDDropdownMenu(caller=caller, items=items, width_mult=4)

    def _select_metric(self, target: str, metric_name: str):
        if target == "main":
            self.app_controller.state.cm_main_metric = metric_name
            if self.main_menu:
                self.main_menu.dismiss()
        else:
            self.app_controller.state.cm_secondary_metric = metric_name
            if self.secondary_menu:
                self.secondary_menu.dismiss()
        self.refresh()

    def _open_main_chart_fullscreen(self, *_args):
        self.app_controller.open_fullscreen_chart(
            title="Condition Monitoring principal",
            subtitle=f"Metrica: {self.app_controller.state.cm_main_metric}",
            series=list(self.main_chart.series),
            x_axis_label=self.main_chart.x_axis_label,
            y_axis_label=self.main_chart.y_axis_label,
            chart_mode=self.main_chart.chart_mode,
            show_legend=self.main_chart.show_legend,
            show_points=self.main_chart.show_points,
            footer="Vista completa para inspeccionar la evolucion de la metrica principal con zoom tactil.",
        )

    def _open_secondary_chart_fullscreen(self, *_args):
        self.app_controller.open_fullscreen_chart(
            title="Condition Monitoring secundario",
            subtitle=f"Metrica: {self.app_controller.state.cm_secondary_metric}",
            series=list(self.secondary_chart.series),
            x_axis_label=self.secondary_chart.x_axis_label,
            y_axis_label=self.secondary_chart.y_axis_label,
            chart_mode=self.secondary_chart.chart_mode,
            show_legend=self.secondary_chart.show_legend,
            show_points=self.secondary_chart.show_points,
            footer="Vista completa para inspeccionar la metrica secundaria con pan y zoom tactil.",
        )

    def refresh(self):
        state = self.app_controller.state
        visible = state.is_multi
        for widget in (self.selector_card, self.main_chart_card, self.secondary_chart_card):
            widget.opacity = 1 if visible else 0
            widget.disabled = not visible
        self.empty_state.opacity = 0 if visible else 1
        self.empty_state.disabled = visible
        if not visible:
            self.main_chart.series = []
            self.secondary_chart.series = []
            return

        self.main_metric_button.text = state.cm_main_metric
        self.secondary_metric_button.text = state.cm_secondary_metric
        self.main_chart.y_axis_label = state.cm_main_metric
        self.secondary_chart.y_axis_label = state.cm_secondary_metric
        main_points, omitted_main = state.condition_monitoring_series(state.cm_main_metric)
        secondary_points, omitted_secondary = state.condition_monitoring_series(state.cm_secondary_metric)
        self.main_chart.series = [{"name": state.cm_main_metric, "color": "#EC6E00", "points": main_points}]
        self.secondary_chart.series = [{"name": state.cm_secondary_metric, "color": "#2E7D32", "points": secondary_points}]
        self.main_warning.text = (
            f"Se omitieron {omitted_main} arranques sin dato valido."
            if omitted_main
            else "Todos los arranques visibles aportan dato valido."
        )
        self.secondary_warning.text = (
            f"Se omitieron {omitted_secondary} arranques sin dato valido."
            if omitted_secondary
            else "Todos los arranques visibles aportan dato valido."
        )


def _chart_controls(chart, fullscreen_callback):
    row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
    row.add_widget(MDFlatButton(text="Zoom -", on_release=lambda *_: chart.zoom_out()))
    row.add_widget(MDFlatButton(text="Reset", on_release=lambda *_: chart.reset_zoom()))
    row.add_widget(MDFlatButton(text="Zoom +", on_release=lambda *_: chart.zoom_in()))
    row.add_widget(MDRaisedButton(text="Pantalla completa", on_release=fullscreen_callback))
    return row
