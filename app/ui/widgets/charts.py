from __future__ import annotations

import math

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.widget import Widget


def _rgba_from_hex(hex_color: str) -> tuple[float, float, float, float]:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return 0.2, 0.2, 0.2, 1.0
    return tuple(int(value[index:index + 2], 16) / 255.0 for index in (0, 2, 4)) + (1.0,)


class MultiSeriesChart(Widget):
    series = ListProperty([])
    stroke_width = NumericProperty(1.8)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw, series=self._redraw)

    def _redraw(self, *_args):
        self.canvas.clear()
        with self.canvas:
            Color(0.93, 0.93, 0.93, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.75, 0.75, 0.75, 1)
            Line(rectangle=(*self.pos, *self.size), width=1)

            all_points = [point for item in self.series for point in item.get("points", [])]
            if not all_points:
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

            left = self.x + self.width * 0.07
            bottom = self.y + self.height * 0.12
            width = self.width * 0.88
            height = self.height * 0.76

            Color(0.82, 0.82, 0.82, 1)
            for ratio in (0.25, 0.5, 0.75):
                y_line = bottom + height * ratio
                Line(points=[left, y_line, left + width, y_line], width=1)

            for item in self.series:
                rgba = _rgba_from_hex(item.get("color", "#EC6E00"))
                chart_points = []
                for x_value, y_value in item.get("points", []):
                    x_pos = left + ((x_value - min_x) / (max_x - min_x)) * width
                    y_pos = bottom + ((y_value - min_y) / (max_y - min_y)) * height
                    chart_points.extend([x_pos, y_pos])
                if len(chart_points) < 4:
                    continue
                Color(*rgba)
                Line(points=chart_points, width=self.stroke_width)
                for index in range(0, len(chart_points), 2):
                    Ellipse(pos=(chart_points[index] - 2.2, chart_points[index + 1] - 2.2), size=(4.4, 4.4))


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
                Color(0.85, 0.85, 0.85, 1)
                Ellipse(pos=(self.center_x - 48, self.center_y - 48), size=(96, 96))
                return

            diameter = min(self.width, self.height) * 0.72
            rect = (self.center_x - diameter / 2, self.center_y - diameter / 2, diameter, diameter)
            start_angle = 0.0
            for segment in self.segments:
                value = max(0.0, float(segment.get("value", 0)))
                if value <= 0:
                    continue
                Color(*_rgba_from_hex(segment.get("color", "#EC6E00")))
                sweep = 360.0 * value / total
                Ellipse(pos=rect[:2], size=rect[2:], angle_start=start_angle, angle_end=start_angle + sweep)
                start_angle += sweep
            Color(1, 1, 1, 1)
            inner = diameter * 0.44
            Ellipse(pos=(self.center_x - inner / 2, self.center_y - inner / 2), size=(inner, inner))
