from __future__ import annotations

from kivy.effects.scroll import ScrollEffect
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
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
        self.page_title = MDLabel(text="Condition Monitoring", bold=True, font_style="H5", adaptive_height=True)
        self.page_subtitle = MDLabel(text="Comparativa compacta y movil.", theme_text_color="Secondary", adaptive_height=True)
        root.add_widget(self.page_title)
        root.add_widget(self.page_subtitle)

        scroll = ScrollView(do_scroll_x=False, effect_cls=ScrollEffect)
        self.scroll = scroll
        self.scroll.bind(scroll_y=lambda *_args: self.app_controller.handle_screen_scroll(self.scroll.scroll_y))
        self.content = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(12), padding=(0, dp(8), 0, dp(24)))
        scroll.add_widget(self.content)
        root.add_widget(scroll)
        self.add_widget(root)

        self.selector_card = SectionCard("Variables")
        self.selector_grid = MDGridLayout(cols=1, adaptive_height=True, spacing=dp(10))
        self.filter_row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
        self.success_filter_button = MDRaisedButton(text="Solo exitosos", on_release=lambda *_: self._toggle_success_filter())
        self.filter_hint = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.filter_row.add_widget(self.success_filter_button)
        self.selector_card.body.add_widget(self.filter_row)
        self.selector_card.body.add_widget(self.filter_hint)
        self.main_selector_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6))
        self.main_add_button = MDRaisedButton(text="+ Principal", on_release=self._open_main_metric_menu)
        self.main_metrics_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6))
        self.secondary_selector_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6))
        self.secondary_add_button = MDRaisedButton(text="+ Secundaria", on_release=self._open_secondary_metric_menu)
        self.secondary_metrics_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6))
        self.main_selector_label = MDLabel(text="Grafica principal", adaptive_height=True, bold=True)
        self.main_selector_box.add_widget(self.main_selector_label)
        self.main_selector_box.add_widget(self.main_add_button)
        self.main_selector_box.add_widget(self.main_metrics_box)
        self.secondary_selector_label = MDLabel(text="Grafica secundaria", adaptive_height=True, bold=True)
        self.secondary_selector_box.add_widget(self.secondary_selector_label)
        self.secondary_selector_box.add_widget(self.secondary_add_button)
        self.secondary_selector_box.add_widget(self.secondary_metrics_box)
        self.selector_grid.add_widget(self.main_selector_box)
        self.selector_grid.add_widget(self.secondary_selector_box)
        self.selector_card.body.add_widget(self.selector_grid)
        self.variables_help_label = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.selector_card.body.add_widget(self.variables_help_label)
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
                "text": self.app_controller.tr_metric(metric_name),
                "viewclass": "OneLineListItem",
                "on_release": lambda name=metric_name, side=target: self._add_metric(side, name),
            }
            for metric_name in SCALAR_FIELDS
            if metric_name not in selected
        ]
        if not items:
            items = [{"text": self.app_controller.tr("cm_no_more_metrics"), "viewclass": "OneLineListItem", "on_release": lambda: None}]
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

    def _toggle_success_filter(self):
        self.app_controller.state.toggle_cm_success_only()
        self.refresh()

    def _render_selected_metrics(self, container, target: str, metrics: list[str]):
        container.clear_widgets()
        for metric_name in metrics:
            row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
            row.add_widget(MDLabel(text=self.app_controller.tr_metric(metric_name), adaptive_height=True))
            row.add_widget(MDFlatButton(text=self.app_controller.tr("cm_remove"), on_release=lambda *_args, side=target, name=metric_name: self._remove_metric(side, name)))
            container.add_widget(row)

    def _open_main_chart_fullscreen(self, *_args):
        metrics = list(self.app_controller.state.cm_main_metrics)
        self.app_controller.open_fullscreen_chart(
            title=self.app_controller.tr("cm_fullscreen_main_title"),
            subtitle=", ".join(self.app_controller.tr_metric(metric) for metric in metrics),
            series=list(self.main_chart.series),
            x_axis_label=self.main_chart.x_axis_label,
            y_axis_label=self.main_chart.y_axis_label,
            chart_mode=self.main_chart.chart_mode,
            show_legend=self.main_chart.show_legend,
            show_points=self.main_chart.show_points,
            x_tick_labels=list(self.main_chart.x_tick_labels),
            allow_point_deletion=True,
            footer=self.app_controller.tr("cm_fullscreen_main_footer"),
        )

    def _open_secondary_chart_fullscreen(self, *_args):
        metrics = list(self.app_controller.state.cm_secondary_metrics)
        self.app_controller.open_fullscreen_chart(
            title=self.app_controller.tr("cm_fullscreen_secondary_title"),
            subtitle=", ".join(self.app_controller.tr_metric(metric) for metric in metrics),
            series=list(self.secondary_chart.series),
            x_axis_label=self.secondary_chart.x_axis_label,
            y_axis_label=self.secondary_chart.y_axis_label,
            chart_mode=self.secondary_chart.chart_mode,
            show_legend=self.secondary_chart.show_legend,
            show_points=self.secondary_chart.show_points,
            x_tick_labels=list(self.secondary_chart.x_tick_labels),
            allow_point_deletion=True,
            footer=self.app_controller.tr("cm_fullscreen_secondary_footer"),
        )

    def refresh(self):
        state = self.app_controller.state
        self.page_title.text = self.app_controller.tr("cm_title")
        self.page_subtitle.text = self.app_controller.tr("cm_subtitle")
        self.selector_card.title_label.text = self.app_controller.tr("cm_variables")
        self.success_filter_button.text = self.app_controller.tr("cm_show_all") if state.cm_success_only else self.app_controller.tr("cm_only_success")
        self.main_add_button.text = self.app_controller.tr("cm_add_main")
        self.secondary_add_button.text = self.app_controller.tr("cm_add_secondary")
        self.main_selector_label.text = self.app_controller.tr("cm_main_chart")
        self.secondary_selector_label.text = self.app_controller.tr("cm_secondary_chart")
        self.variables_help_label.text = self.app_controller.tr("cm_variables_help")
        self.empty_state.text_widget.text = self.app_controller.tr("cm_empty")
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
        filtered_indices = state.condition_monitoring_filtered_indices()
        self.success_filter_button.text = self.app_controller.tr("cm_show_all") if state.cm_success_only else self.app_controller.tr("cm_only_success")
        self.filter_hint.text = (
            self.app_controller.tr("cm_filter_success", count=len(filtered_indices))
            if state.cm_success_only
            else self.app_controller.tr("cm_filter_multi", count=len(filtered_indices))
        )

        self.main_chart_card.title_label.text = state.cm_title([self.app_controller.tr_metric(item) for item in state.cm_main_metrics], self.app_controller.tr("cm_main_chart"))
        self.secondary_chart_card.title_label.text = state.cm_title([self.app_controller.tr_metric(item) for item in state.cm_secondary_metrics], self.app_controller.tr("cm_secondary_chart"))
        x_axis_label = state.condition_monitoring_x_axis_label()
        x_tick_labels = state.condition_monitoring_x_tick_labels()
        self.main_chart.x_axis_label = x_axis_label
        self.main_chart.y_axis_label = state.cm_axis_label([self.app_controller.tr_metric(item) for item in state.cm_main_metrics])
        self.main_chart.x_tick_labels = x_tick_labels
        self.main_chart.allow_point_deletion = False
        self.main_chart.max_points = max(600, len(filtered_indices) * 3)
        self.secondary_chart.x_axis_label = x_axis_label
        self.secondary_chart.y_axis_label = state.cm_axis_label([self.app_controller.tr_metric(item) for item in state.cm_secondary_metrics])
        self.secondary_chart.x_tick_labels = x_tick_labels
        self.secondary_chart.allow_point_deletion = False
        self.secondary_chart.max_points = max(600, len(filtered_indices) * 3)

        main_series = []
        main_messages = []
        for index, metric_name in enumerate(state.cm_main_metrics):
            points, omitted = state.condition_monitoring_series(metric_name)
            translated_metric = self.app_controller.tr_metric(metric_name)
            main_series.append({"name": translated_metric, "color": CM_COLORS[index % len(CM_COLORS)], "points": points})
            main_messages.append(self.app_controller.tr("cm_warning_omitted", metric=translated_metric, count=omitted) if omitted else self.app_controller.tr("cm_warning_ok", metric=translated_metric))
        self.main_chart.series = main_series
        self.main_warning.text = " | ".join(main_messages)

        secondary_series = []
        secondary_messages = []
        for index, metric_name in enumerate(state.cm_secondary_metrics):
            points, omitted = state.condition_monitoring_series(metric_name)
            translated_metric = self.app_controller.tr_metric(metric_name)
            secondary_series.append({"name": translated_metric, "color": CM_COLORS[index % len(CM_COLORS)], "points": points})
            secondary_messages.append(self.app_controller.tr("cm_warning_omitted", metric=translated_metric, count=omitted) if omitted else self.app_controller.tr("cm_warning_ok", metric=translated_metric))
        self.secondary_chart.series = secondary_series
        self.secondary_warning.text = " | ".join(secondary_messages)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        landscape = self.width > self.height and self.width > dp(700)
        self.selector_grid.cols = 2 if landscape else 1
        self.main_chart.height = dp(300) if landscape else dp(240)
        self.secondary_chart.height = dp(300) if landscape else dp(240)


def _chart_controls(chart, fullscreen_callback):
    row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
    row.add_widget(MDFlatButton(text="Reset", on_release=lambda *_: chart.reset_zoom()))
    row.add_widget(MDRaisedButton(text="Pantalla completa", on_release=fullscreen_callback))
    return row
