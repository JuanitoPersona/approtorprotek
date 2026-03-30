from __future__ import annotations

import math

from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.widget import Widget


def _rgba_from_hex(hex_color: str) -> tuple[float, float, float, float]:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return 0.2, 0.2, 0.2, 1.0
    return tuple(int(value[index:index + 2], 16) / 255.0 for index in (0, 2, 4)) + (1.0,)


def _draw_text(canvas, text: str, x: float, y: float, color=(0.2, 0.2, 0.2, 1.0), font_size: int = 12):
    label = CoreLabel(text=str(text), font_size=font_size, color=color)
    label.refresh()
    texture = label.texture
    with canvas:
        Color(1, 1, 1, 0)
        Rectangle(texture=texture, pos=(x, y), size=texture.size)
    return texture.size


def _downsample_points(points: list[tuple[float, float]], max_points: int) -> list[tuple[float, float]]:
    if max_points <= 0 or len(points) <= max_points:
        return points
    step = max(1, int(math.ceil(len(points) / max_points)))
    sampled = points[::step]
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled


class MultiSeriesChart(Widget):
    series = ListProperty([])
    stroke_width = NumericProperty(1.8)
    x_axis_label = StringProperty("")
    y_axis_label = StringProperty("")
    show_legend = BooleanProperty(True)
    max_points = NumericProperty(180)
    zoom_factor = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            series=self._redraw,
            x_axis_label=self._redraw,
            y_axis_label=self._redraw,
            show_legend=self._redraw,
            zoom_factor=self._redraw,
        )

    def zoom_in(self):
        self.zoom_factor = min(8.0, self.zoom_factor * 1.35)

    def zoom_out(self):
        self.zoom_factor = max(1.0, self.zoom_factor / 1.35)

    def reset_zoom(self):
        self.zoom_factor = 1.0

    def _redraw(self, *_args):
        self.canvas.clear()
        with self.canvas:
            Color(0.96, 0.96, 0.96, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.82, 0.82, 0.82, 1)
            Line(rectangle=(*self.pos, *self.size), width=1)

        all_points = [point for item in self.series for point in item.get("points", [])]
        if not all_points:
            _draw_text(self.canvas, "Sin datos", self.x + 16, self.center_y - 8)
            return

        xs = [point[0] for point in all_points]
        ys = [point[1] for point in all_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        if math.isclose(min_x, max_x):
            max_x += 1.0
        if math.isclose(min_y, max_y):
            margin = 1.0 if min_y == 0 else abs(min_y) * 0.1
            min_y -= margin
            max_y += margin

        if self.zoom_factor > 1.0:
            span_x = (max_x - min_x) / self.zoom_factor
            span_y = (max_y - min_y) / self.zoom_factor
            center_x = (min_x + max_x) / 2.0
            center_y = (min_y + max_y) / 2.0
            min_x = center_x - span_x / 2.0
            max_x = center_x + span_x / 2.0
            min_y = center_y - span_y / 2.0
            max_y = center_y + span_y / 2.0

        left = self.x + 54
        bottom = self.y + 40
        top_padding = 34 if self.show_legend else 18
        width = max(10.0, self.width - 70)
        height = max(10.0, self.height - bottom + self.y - top_padding)
        top = bottom + height

        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=(left, bottom), size=(width, height))
            Color(0.75, 0.75, 0.75, 1)
            Line(points=[left, bottom, left, top], width=1)
            Line(points=[left, bottom, left + width, bottom], width=1)

            for ratio in (0.25, 0.5, 0.75):
                y_line = bottom + height * ratio
                x_line = left + width * ratio
                Color(0.88, 0.88, 0.88, 1)
                Line(points=[left, y_line, left + width, y_line], width=1)
                Line(points=[x_line, bottom, x_line, top], width=1)

        self._draw_ticks(left, bottom, width, height, min_x, max_x, min_y, max_y)
        self._draw_axis_labels(left, bottom, width, top)
        if self.show_legend:
            self._draw_legend(left, top + 8)

        for item in self.series:
            rgba = _rgba_from_hex(item.get("color", "#EC6E00"))
            visible_points = [
                (x_value, y_value)
                for x_value, y_value in item.get("points", [])
                if min_x <= x_value <= max_x and min_y <= y_value <= max_y
            ]
            visible_points = _downsample_points(visible_points, int(self.max_points))
            chart_points = []
            for x_value, y_value in visible_points:
                x_pos = left + ((x_value - min_x) / (max_x - min_x)) * width
                y_pos = bottom + ((y_value - min_y) / (max_y - min_y)) * height
                chart_points.extend([x_pos, y_pos])
            if len(chart_points) < 4:
                continue
            with self.canvas:
                Color(*rgba)
                Line(points=chart_points, width=self.stroke_width)
                for index in range(0, len(chart_points), 2):
                    Ellipse(pos=(chart_points[index] - 2.2, chart_points[index + 1] - 2.2), size=(4.4, 4.4))

    def _draw_ticks(self, left, bottom, width, height, min_x, max_x, min_y, max_y):
        x_ticks = [min_x, (min_x + max_x) / 2.0, max_x]
        y_ticks = [min_y, (min_y + max_y) / 2.0, max_y]
        for value in x_ticks:
            x_pos = left + ((value - min_x) / (max_x - min_x)) * width
            _draw_text(self.canvas, _format_tick(value), x_pos - 14, bottom - 22, font_size=11)
        for value in y_ticks:
            y_pos = bottom + ((value - min_y) / (max_y - min_y)) * height
            _draw_text(self.canvas, _format_tick(value), self.x + 4, y_pos - 6, font_size=11)

    def _draw_axis_labels(self, left, bottom, width, top):
        if self.x_axis_label:
            size = _draw_text(self.canvas, self.x_axis_label, 0, 0, font_size=12)
            _draw_text(self.canvas, self.x_axis_label, left + (width - size[0]) / 2.0, self.y + 6, font_size=12)
        if self.y_axis_label:
            _draw_text(self.canvas, self.y_axis_label, self.x + 4, top + 8, font_size=12)

    def _draw_legend(self, left, baseline_y):
        cursor_x = left
        for item in self.series:
            rgba = _rgba_from_hex(item.get("color", "#EC6E00"))
            with self.canvas:
                Color(*rgba)
                Line(points=[cursor_x, baseline_y + 8, cursor_x + 14, baseline_y + 8], width=2)
            size = _draw_text(self.canvas, item.get("name", "Serie"), cursor_x + 18, baseline_y, font_size=11)
            cursor_x += 24 + size[0]


class PieChartWidget(Widget):
    segments = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw, segments=self._redraw)

    def _redraw(self, *_args):
        self.canvas.clear()
        with self.canvas:
            Color(0.96, 0.96, 0.96, 1)
            Rectangle(pos=self.pos, size=self.size)

        total = sum(max(0.0, float(segment.get("value", 0))) for segment in self.segments)
        if total <= 0:
            with self.canvas:
                Color(0.85, 0.85, 0.85, 1)
                Ellipse(pos=(self.center_x - 48, self.center_y - 48), size=(96, 96))
            _draw_text(self.canvas, "Sin datos", self.center_x - 24, self.center_y - 8)
            return

        diameter = min(self.width, self.height) * 0.72
        center_x = self.center_x
        center_y = self.center_y
        rect = (center_x - diameter / 2, center_y - diameter / 2, diameter, diameter)
        start_angle = 0.0
        for segment in self.segments:
            value = max(0.0, float(segment.get("value", 0)))
            if value <= 0:
                continue
            rgba = _rgba_from_hex(segment.get("color", "#EC6E00"))
            sweep = 360.0 * value / total
            with self.canvas:
                Color(*rgba)
                Ellipse(pos=rect[:2], size=rect[2:], angle_start=start_angle, angle_end=start_angle + sweep)
            percentage = 100.0 * value / total
            if percentage >= 4.0:
                angle_mid = math.radians(start_angle + sweep / 2.0)
                label_radius = diameter * 0.28
                label_x = center_x + math.cos(angle_mid) * label_radius
                label_y = center_y + math.sin(angle_mid) * label_radius
                text = f"{percentage:.0f}%"
                text_size = _draw_text(self.canvas, text, 0, 0, color=(1, 1, 1, 1), font_size=12)
                _draw_text(
                    self.canvas,
                    text,
                    label_x - text_size[0] / 2.0,
                    label_y - text_size[1] / 2.0,
                    color=(1, 1, 1, 1),
                    font_size=12,
                )
            start_angle += sweep

        with self.canvas:
            Color(1, 1, 1, 1)
            inner = diameter * 0.44
            Ellipse(pos=(center_x - inner / 2, center_y - inner / 2), size=(inner, inner))
        total_size = _draw_text(self.canvas, str(int(total)), 0, 0, font_size=14)
        _draw_text(self.canvas, str(int(total)), center_x - total_size[0] / 2.0, center_y - total_size[1] / 2.0, font_size=14)


def _format_tick(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"
