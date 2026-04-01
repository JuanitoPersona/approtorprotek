from __future__ import annotations

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.screen import MDScreen
from kivy.uix.widget import Widget

from ..widgets.charts import MultiSeriesChart


class DrawingOverlay(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draw_mode = False
        self.strokes: list[list[float]] = []
        self._active_lines: dict[int, Line] = {}

    def on_touch_down(self, touch):
        if not self.draw_mode or not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        with self.canvas:
            Color(0.925, 0.431, 0.0, 0.95)
            line = Line(points=[touch.x, touch.y], width=2.2)
        touch.grab(self)
        self._active_lines[id(touch)] = line
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        line = self._active_lines.get(id(touch))
        if line is not None:
            line.points = list(line.points) + [touch.x, touch.y]
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        line = self._active_lines.pop(id(touch), None)
        if line is not None and len(line.points) >= 4:
            self.strokes.append(list(line.points))
        return True

    def clear_drawings(self):
        self.canvas.clear()
        self.strokes = []
        self._active_lines.clear()


class FullscreenChartScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "fullscreen_chart"
        self._chart_title = "chart"
        self._draw_mode = False

        root = MDBoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        self.controls = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(8), row_default_height=dp(42), row_force_default=True)
        self.reset_button = MDFlatButton(text="", on_release=lambda *_: self.chart.reset_zoom())
        self.delete_button = MDFlatButton(text="", on_release=lambda *_: self._toggle_delete_mode())
        self.restore_button = MDFlatButton(text="", on_release=lambda *_: self.chart.restore_points())
        self.draw_button = MDFlatButton(text="", on_release=lambda *_: self._toggle_draw_mode())
        self.clear_drawings_button = MDFlatButton(text="", on_release=lambda *_: self._clear_drawings())
        self.share_button = MDFlatButton(text="", on_release=lambda *_: self._share_chart())
        self.close_button = MDRaisedButton(text="", on_release=lambda *_: self.app_controller.close_fullscreen_chart())
        for widget in (
            self.reset_button,
            self.delete_button,
            self.restore_button,
            self.draw_button,
            self.clear_drawings_button,
            self.share_button,
            self.close_button,
        ):
            widget.size_hint_x = 1
            self.controls.add_widget(widget)
        root.add_widget(self.controls)

        self.chart_container = FloatLayout(size_hint=(1, 1))
        self.chart = MultiSeriesChart(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.chart.enable_touch_navigation = True
        self.overlay = DrawingOverlay(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.chart_container.add_widget(self.chart)
        self.chart_container.add_widget(self.overlay)
        root.add_widget(self.chart_container)
        self.add_widget(root)
        self.bind(size=lambda *_: self._apply_responsive_layout())
        self._apply_responsive_layout()

    def _toggle_delete_mode(self):
        if self._draw_mode:
            self._set_draw_mode(False)
        self.chart.toggle_delete_mode()
        self.delete_button.text = self.app_controller.tr("fullscreen_delete_exit") if self.chart.delete_mode else self.app_controller.tr("fullscreen_delete")

    def _toggle_draw_mode(self):
        self._set_draw_mode(not self._draw_mode)

    def _clear_drawings(self):
        self.overlay.clear_drawings()
        self._set_draw_mode(self._draw_mode)

    def _set_draw_mode(self, enabled: bool):
        self._draw_mode = bool(enabled)
        self.overlay.draw_mode = self._draw_mode
        self.chart.enable_touch_navigation = not self._draw_mode
        if self._draw_mode and self.chart.delete_mode:
            self.chart.delete_mode = False
            self.delete_button.text = self.app_controller.tr("fullscreen_delete")
        self.draw_button.text = self.app_controller.tr("draw_exit") if self._draw_mode else self.app_controller.tr("draw")
        self.clear_drawings_button.disabled = not (self._draw_mode or bool(self.overlay.strokes))
        self.clear_drawings_button.opacity = 1 if (self._draw_mode or bool(self.overlay.strokes)) else 0.6

    def _share_chart(self):
        self.app_controller.share_chart_widget(self.chart_container, self._chart_title)

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
        self.reset_button.text = self.app_controller.tr("reset")
        self.delete_button.text = self.app_controller.tr("fullscreen_delete")
        self.restore_button.text = self.app_controller.tr("restore")
        self.draw_button.text = self.app_controller.tr("draw")
        self.clear_drawings_button.text = self.app_controller.tr("clear_drawings")
        self.share_button.text = self.app_controller.tr("share")
        self.close_button.text = self.app_controller.tr("close")
        self._chart_title = title
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
        self.delete_button.disabled = not allow_point_deletion
        self.delete_button.opacity = 1 if allow_point_deletion else 0
        self.restore_button.disabled = not allow_point_deletion
        self.restore_button.opacity = 1 if allow_point_deletion else 0
        self.overlay.clear_drawings()
        self._set_draw_mode(False)
        self.chart.reset_zoom()
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        landscape = self.width > self.height and self.width > dp(700)
        self.chart.stroke_width = 2.2 if landscape else 1.8
        self.controls.cols = 7 if landscape else 3

    def apply_theme(self, palette: dict):
        self.md_bg_color = palette["background"]
