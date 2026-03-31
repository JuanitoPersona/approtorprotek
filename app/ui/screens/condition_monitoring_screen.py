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

CM_COLORS = ["#EC6E00", "#2E7D32", "#1976D2", "#7B1FA2"]


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
        self.main_add_button = MDRaisedButton(text="+ Principal", on_release=self._open_main_metric_menu)
        self.main_metrics_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6))
        self.secondary_add_button = MDRaisedButton(text="+ Secundaria", on_release=self._open_secondary_metric_menu)
        self.secondary_metrics_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6))
        self.selector_card.body.add_widget(MDLabel(text="Grafica principal", adaptive_height=True, bold=True))
        self.selector_card.body.add_widget(self.main_add_button)
        self.selector_card.body.add_widget(self.main_metrics_box)
        self.selector_card.body.add_widget(MDLabel(text="Grafica secundaria", adaptive_height=True, bold=True))
        self.selector_card.body.add_widget(self.secondary_add_button)
        self.selector_card.body.add_widget(self.secondary_metrics_box)
        self.selector_card.body.add_widget(
            MDLabel(
                text="Puedes anadir hasta 4 variables por grafica. Usa el boton + y quita las que no necesites.",
                adaptive_height=True,
                theme_text_color="Secondary",
            )
        )
        self.content.add_widget(self.selector_card)

        self.main_chart_card = SectionCard("Variables principales")
        self.main_chart = MultiSeriesChart(size_hint_y=None, height=dp(240), x_axis_label="Arranque", y_axis_label="Valor", show_points=True)
        self.main_chart.open_fullscreen_callback = self._open_main_chart_fullscreen
        self.main_chart_card.body.add_widget(_chart_controls(self.main_chart, self._open_main_chart_fullscreen))
        self.main_warning = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.main_chart_card.body.add_widget(self.main_chart)
        self.main_chart_card.body.add_widget(self.main_warning)
        self.content.add_widget(self.main_chart_card)

        self.secondary_chart_card = SectionCard("Variables secundarias")
        self.secondary_chart = MultiSeriesChart(size_hint_y=None, height=dp(240), x_axis_label="Arranque", y_axis_label="Valor", show_points=True)
        self.secondary_chart.open_fullscreen_callback = self._open_secondary_chart_fullscreen
        self.secondary_chart_card.body.add_widget(_chart_controls(self.secondary_chart, self._open_secondary_chart_fullscreen))
        self.secondary_warning = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.secondary_chart_card.body.add_widget(self.secondary_chart)
        self.secondary_chart_card.body.add_widget(self.secondary_warning)
        self.content.add_widget(self.secondary_chart_card)

        self.empty_state = EmptyState("Condition Monitoring solo esta disponible si el CSV contiene multiples arranques.")
        self.content.add_widget(self.empty_state)
        self.bind(size=lambda *_: self._apply_responsive_layout())
        self._apply_responsive_layout()

    def _open_main_metric_menu(self, *_args):
        self.main_menu = self._build_metric_menu(self.main_add_button, "main")
        self.main_menu.open()

    def _open_secondary_metric_menu(self, *_args):
        self.secondary_menu = self._build_metric_menu(self.secondary_add_button, "secondary")
        self.secondary_menu.open()

    def _build_metric_menu(self, caller, target: str):
        selected = set(self.app_controller.state.cm_main_metrics if target == "main" else self.app_controller.state.cm_secondary_metrics)
        items = [
            {
                "text": metric_name,
                "viewclass": "OneLineListItem",
                "on_release": lambda name=metric_name, side=target: self._add_metric(side, name),
            }
            for metric_name in SCALAR_FIELDS
            if metric_name not in selected
        ]
        if not items:
            items = [{"text": "No hay mas variables disponibles", "viewclass": "OneLineListItem", "on_release": lambda: None}]
        return MDDropdownMenu(caller=caller, items=items, width_mult=5)

    def _add_metric(self, target: str, metric_name: str):
        self.app_controller.state.add_cm_metric(target, metric_name)
        if target == "main" and self.main_menu:
            self.main_menu.dismiss()
        if target == "secondary" and self.secondary_menu:
            self.secondary_menu.dismiss()
        self.refresh()

    def _remove_metric(self, target: str, metric_name: str):
        self.app_controller.state.remove_cm_metric(target, metric_name)
        self.refresh()

    def _render_selected_metrics(self, container, target: str, metrics: list[str]):
        container.clear_widgets()
        for metric_name in metrics:
            row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
            row.add_widget(MDLabel(text=metric_name, adaptive_height=True))
            row.add_widget(MDFlatButton(text="Quitar", on_release=lambda *_args, side=target, name=metric_name: self._remove_metric(side, name)))
            container.add_widget(row)

    def _open_main_chart_fullscreen(self, *_args):
        metrics = list(self.app_controller.state.cm_main_metrics)
        self.app_controller.open_fullscreen_chart(
            title="Condition Monitoring principal",
            subtitle=", ".join(metrics),
            series=list(self.main_chart.series),
            x_axis_label=self.main_chart.x_axis_label,
            y_axis_label=self.main_chart.y_axis_label,
            chart_mode=self.main_chart.chart_mode,
            show_legend=self.main_chart.show_legend,
            show_points=self.main_chart.show_points,
            footer="Vista completa para inspeccionar varias metricas en paralelo con zoom tactil.",
        )

    def _open_secondary_chart_fullscreen(self, *_args):
        metrics = list(self.app_controller.state.cm_secondary_metrics)
        self.app_controller.open_fullscreen_chart(
            title="Condition Monitoring secundario",
            subtitle=", ".join(metrics),
            series=list(self.secondary_chart.series),
            x_axis_label=self.secondary_chart.x_axis_label,
            y_axis_label=self.secondary_chart.y_axis_label,
            chart_mode=self.secondary_chart.chart_mode,
            show_legend=self.secondary_chart.show_legend,
            show_points=self.secondary_chart.show_points,
            footer="Vista completa para comparar metricas secundarias con pan y zoom tactil.",
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

        self._render_selected_metrics(self.main_metrics_box, "main", state.cm_main_metrics)
        self._render_selected_metrics(self.secondary_metrics_box, "secondary", state.cm_secondary_metrics)

        self.main_chart_card.title_label.text = state.cm_title(state.cm_main_metrics, "Variables principales")
        self.secondary_chart_card.title_label.text = state.cm_title(state.cm_secondary_metrics, "Variables secundarias")
        self.main_chart.y_axis_label = state.cm_axis_label(state.cm_main_metrics)
        self.secondary_chart.y_axis_label = state.cm_axis_label(state.cm_secondary_metrics)

        main_series = []
        main_messages = []
        for index, metric_name in enumerate(state.cm_main_metrics):
            points, omitted = state.condition_monitoring_series(metric_name)
            main_series.append({"name": metric_name, "color": CM_COLORS[index % len(CM_COLORS)], "points": points})
            main_messages.append(f"{metric_name}: {omitted} omitidos" if omitted else f"{metric_name}: OK")
        self.main_chart.series = main_series
        self.main_warning.text = " | ".join(main_messages)

        secondary_series = []
        secondary_messages = []
        for index, metric_name in enumerate(state.cm_secondary_metrics):
            points, omitted = state.condition_monitoring_series(metric_name)
            secondary_series.append({"name": metric_name, "color": CM_COLORS[index % len(CM_COLORS)], "points": points})
            secondary_messages.append(f"{metric_name}: {omitted} omitidos" if omitted else f"{metric_name}: OK")
        self.secondary_chart.series = secondary_series
        self.secondary_warning.text = " | ".join(secondary_messages)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        landscape = self.width > self.height and self.width > dp(700)
        self.main_chart.height = dp(300) if landscape else dp(240)
        self.secondary_chart.height = dp(300) if landscape else dp(240)


def _chart_controls(chart, fullscreen_callback):
    row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
    row.add_widget(MDFlatButton(text="Zoom -", on_release=lambda *_: chart.zoom_out()))
    row.add_widget(MDFlatButton(text="Reset", on_release=lambda *_: chart.reset_zoom()))
    row.add_widget(MDFlatButton(text="Zoom +", on_release=lambda *_: chart.zoom_in()))
    row.add_widget(MDRaisedButton(text="Pantalla completa", on_release=fullscreen_callback))
    return row
