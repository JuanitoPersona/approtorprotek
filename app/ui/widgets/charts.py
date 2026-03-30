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


def _text_texture(text: str, color=(0.2, 0.2, 0.2, 1.0), font_size: int = 12):
    label = CoreLabel(text=str(text), font_size=font_size, color=color)
    label.refresh()
    return label.texture


def _draw_text(canvas, text: str, x: float, y: float, color=(0.2, 0.2, 0.2, 1.0), font_size: int = 12):
    texture = _text_texture(text, color=color, font_size=font_size)
    with canvas:
        Color(1, 1, 1, 0)
        Rectangle(texture=texture, pos=(x, y), size=texture.size)
    return texture.size


def _downsample_points(points: list[tuple[float, float]], max_points: int) -> list[tuple[float, float]]:
    if max_points <= 0 or len(points) <= max_points:
        return points
    step = max(1, int(math.ceil(len(points) / max_points)))
    sampled = points[::step]
    if sampled and sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled


def _nice_number(value: float, rounding: bool) -> float:
    if value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    fraction = value / (10 ** exponent)
    if rounding:
        if fraction < 1.5:
            nice_fraction = 1
        elif fraction < 3:
            nice_fraction = 2
        elif fraction < 7:
            nice_fraction = 5
        else:
            nice_fraction = 10
    else:
        if fraction <= 1:
            nice_fraction = 1
        elif fraction <= 2:
            nice_fraction = 2
        elif fraction <= 5:
            nice_fraction = 5
        else:
            nice_fraction = 10
    return nice_fraction * (10 ** exponent)


def _nice_ticks(min_value: float, max_value: float, target_count: int = 5) -> list[float]:
    span = max_value - min_value
    if math.isclose(span, 0.0):
        return [min_value]
    step = _nice_number(span / max(1, target_count - 1), rounding=True)
    graph_min = math.floor(min_value / step) * step
    graph_max = math.ceil(max_value / step) * step
    ticks = []
    value = graph_min
    guard = 0
    while value <= graph_max + step * 0.5 and guard < 32:
        ticks.append(float(value))
        value += step
        guard += 1
    return ticks


class MultiSeriesChart(Widget):
    series = ListProperty([])
    stroke_width = NumericProperty(1.8)
    x_axis_label = StringProperty("")
    y_axis_label = StringProperty("")
    show_legend = BooleanProperty(True)
    max_points = NumericProperty(240)
    zoom_factor = NumericProperty(1.0)
    pan_x = NumericProperty(0.5)
    pan_y = NumericProperty(0.5)
    chart_mode = StringProperty("line")
    show_points = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._full_bounds = (0.0, 1.0, 0.0, 1.0)
        self._plot_rect = (0.0, 0.0, 1.0, 1.0)
        self._legend_rows: list[list[dict]] = []
        self._active_touches: dict[int, tuple[float, float]] = {}
        self._gesture_start_distance: float | None = None
        self._gesture_start_zoom = 1.0
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            series=self._redraw,
            x_axis_label=self._redraw,
            y_axis_label=self._redraw,
            show_legend=self._redraw,
            zoom_factor=self._redraw,
            pan_x=self._redraw,
            pan_y=self._redraw,
            chart_mode=self._redraw,
            show_points=self._redraw,
        )

    def zoom_in(self):
        self._set_zoom(self.zoom_factor * 1.35)

    def zoom_out(self):
        self._set_zoom(self.zoom_factor / 1.35)

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.pan_x = 0.5
        self.pan_y = 0.5

    def _set_zoom(self, value: float):
        self.zoom_factor = min(12.0, max(1.0, float(value)))
        self.pan_x = min(1.0, max(0.0, self.pan_x))
        self.pan_y = min(1.0, max(0.0, self.pan_y))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self._touch_in_plot(touch.pos):
            touch.grab(self)
            self._active_touches[id(touch)] = touch.pos
            if len(self._active_touches) == 2:
                self._gesture_start_distance = self._current_touch_distance()
                self._gesture_start_zoom = self.zoom_factor
            if getattr(touch, "is_double_tap", False):
                self.reset_zoom()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        previous = self._active_touches.get(id(touch), touch.ppos)
        self._active_touches[id(touch)] = touch.pos
        if len(self._active_touches) >= 2:
            if self._gesture_start_distance:
                current_distance = self._current_touch_distance()
                if current_distance > 0:
                    self._set_zoom(self._gesture_start_zoom * (current_distance / self._gesture_start_distance))
            return True

        dx = touch.x - previous[0]
        dy = touch.y - previous[1]
        self._pan_from_pixels(dx, dy)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        self._active_touches.pop(id(touch), None)
        if len(self._active_touches) < 2:
            self._gesture_start_distance = None
            self._gesture_start_zoom = self.zoom_factor
        return True

    def _touch_in_plot(self, pos) -> bool:
        left, bottom, width, height = self._plot_rect
        x_pos, y_pos = pos
        return left <= x_pos <= left + width and bottom <= y_pos <= bottom + height

    def _current_touch_distance(self) -> float:
        points = list(self._active_touches.values())
        if len(points) < 2:
            return 0.0
        (x1, y1), (x2, y2) = points[:2]
        return math.hypot(x2 - x1, y2 - y1)

    def _pan_from_pixels(self, dx: float, dy: float):
        full_min_x, full_max_x, full_min_y, full_max_y = self._full_bounds
        full_range_x = max(1e-9, full_max_x - full_min_x)
        full_range_y = max(1e-9, full_max_y - full_min_y)
        span_x = full_range_x / self.zoom_factor
        span_y = full_range_y / self.zoom_factor
        extra_x = max(0.0, full_range_x - span_x)
        extra_y = max(0.0, full_range_y - span_y)
        plot_width = max(1.0, self._plot_rect[2])
        plot_height = max(1.0, self._plot_rect[3])
        if extra_x > 0:
            data_dx = dx / plot_width * span_x
            self.pan_x = min(1.0, max(0.0, self.pan_x - data_dx / extra_x))
        if extra_y > 0:
            data_dy = dy / plot_height * span_y
            self.pan_y = min(1.0, max(0.0, self.pan_y - data_dy / extra_y))

    def _redraw(self, *_args):
        self.canvas.clear()
        self._legend_rows = self._build_legend_rows()
        legend_height = (18 * len(self._legend_rows) + 10) if self.show_legend and self._legend_rows else 0

        left = self.x + 72
        right_padding = 18
        bottom = self.y + 56
        top_padding = 26 + legend_height
        width = max(10.0, self.width - (left - self.x) - right_padding)
        height = max(10.0, self.height - (bottom - self.y) - top_padding)
        top = bottom + height
        self._plot_rect = (left, bottom, width, height)

        with self.canvas:
            Color(0.96, 0.96, 0.96, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.82, 0.82, 0.82, 1)
            Line(rectangle=(*self.pos, *self.size), width=1)

        all_points = self._extract_points()
        if not all_points:
            _draw_text(self.canvas, "Sin datos", self.x + 16, self.center_y - 8)
            return

        self._full_bounds = self._compute_full_bounds(all_points)
        min_x, max_x, min_y, max_y = self._current_view_bounds()

        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=(left, bottom), size=(width, height))

        self._draw_grid_and_ticks(left, bottom, width, height, min_x, max_x, min_y, max_y)
        self._draw_axis_labels(left, bottom, width, top)
        if self.show_legend and self._legend_rows:
            self._draw_legend(left, top + 10, width)

        if self.chart_mode == "bar":
            self._draw_bar_series(left, bottom, width, height, min_x, max_x, min_y, max_y)
        else:
            self._draw_line_series(left, bottom, width, height, min_x, max_x, min_y, max_y)

    def _extract_points(self) -> list[tuple[float, float]]:
        if self.chart_mode == "bar":
            points: list[tuple[float, float]] = []
            for item in self.series:
                for idx, point in enumerate(item.get("points", [])):
                    points.append((float(idx), float(point[1])))
            return points
        return [point for item in self.series for point in item.get("points", [])]

    def _compute_full_bounds(self, all_points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
        xs = [point[0] for point in all_points]
        ys = [point[1] for point in all_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        if self.chart_mode == "bar":
            min_x -= 0.5
            max_x += 0.5
        if math.isclose(min_x, max_x):
            max_x += 1.0
        if math.isclose(min_y, max_y):
            margin = 1.0 if min_y == 0 else abs(min_y) * 0.1
            min_y -= margin
            max_y += margin
        if min_y > 0:
            min_y = 0.0
        elif max_y < 0:
            max_y = 0.0
        else:
            pad = (max_y - min_y) * 0.08 or 1.0
            min_y -= pad
            max_y += pad
        return min_x, max_x, min_y, max_y

    def _current_view_bounds(self) -> tuple[float, float, float, float]:
        full_min_x, full_max_x, full_min_y, full_max_y = self._full_bounds
        full_range_x = max(1e-9, full_max_x - full_min_x)
        full_range_y = max(1e-9, full_max_y - full_min_y)
        span_x = full_range_x / self.zoom_factor
        span_y = full_range_y / self.zoom_factor
        extra_x = max(0.0, full_range_x - span_x)
        extra_y = max(0.0, full_range_y - span_y)
        min_x = full_min_x + extra_x * self.pan_x
        min_y = full_min_y + extra_y * self.pan_y
        return min_x, min_x + span_x, min_y, min_y + span_y

    def _draw_grid_and_ticks(self, left, bottom, width, height, min_x, max_x, min_y, max_y):
        x_ticks = self._bar_ticks(min_x, max_x) if self.chart_mode == "bar" else _nice_ticks(min_x, max_x, target_count=5)
        y_ticks = _nice_ticks(min_y, max_y, target_count=5)

        with self.canvas:
            Color(0.74, 0.74, 0.74, 1)
            Line(points=[left, bottom, left, bottom + height], width=1.1)
            Line(points=[left, bottom, left + width, bottom], width=1.1)

        for value in y_ticks:
            if value < min_y - 1e-9 or value > max_y + 1e-9:
                continue
            y_pos = bottom + ((value - min_y) / (max_y - min_y)) * height
            with self.canvas:
                Color(0.90, 0.90, 0.90, 1)
                Line(points=[left, y_pos, left + width, y_pos], width=1)
                Color(0.62, 0.62, 0.62, 1)
                Line(points=[left - 4, y_pos, left, y_pos], width=1)
            size = _draw_text(self.canvas, _format_tick(value), 0, 0, font_size=11)
            _draw_text(self.canvas, _format_tick(value), left - size[0] - 8, y_pos - size[1] / 2.0, font_size=11)

        for tick in x_ticks:
            if self.chart_mode == "bar":
                index = int(tick)
                label = self._bar_tick_label(index)
                x_pos = left + (((index + 0.5) - min_x) / (max_x - min_x)) * width
            else:
                if tick < min_x - 1e-9 or tick > max_x + 1e-9:
                    continue
                label = _format_tick(tick)
                x_pos = left + ((tick - min_x) / (max_x - min_x)) * width
            with self.canvas:
                Color(0.90, 0.90, 0.90, 1)
                Line(points=[x_pos, bottom, x_pos, bottom + height], width=1)
                Color(0.62, 0.62, 0.62, 1)
                Line(points=[x_pos, bottom, x_pos, bottom - 4], width=1)
            size = _draw_text(self.canvas, label, 0, 0, font_size=10)
            _draw_text(self.canvas, label, x_pos - size[0] / 2.0, bottom - size[1] - 8, font_size=10)

    def _draw_axis_labels(self, left, bottom, width, top):
        if self.x_axis_label:
            size = _draw_text(self.canvas, self.x_axis_label, 0, 0, font_size=12)
            _draw_text(self.canvas, self.x_axis_label, left + (width - size[0]) / 2.0, self.y + 10, font_size=12)
        if self.y_axis_label:
            _draw_text(self.canvas, self.y_axis_label, left, top + 8, font_size=12)

    def _build_legend_rows(self) -> list[list[dict]]:
        if not self.show_legend:
            return []
        rows: list[list[dict]] = [[]]
        current_width = 0.0
        max_width = max(120.0, self.width - 120.0)
        for item in self.series:
            label = str(item.get("name", "Serie"))
            texture = _text_texture(label, font_size=11)
            item_width = 26 + texture.size[0]
            if rows[-1] and current_width + item_width > max_width:
                rows.append([])
                current_width = 0.0
            rows[-1].append({"name": label, "color": item.get("color", "#EC6E00"), "width": item_width})
            current_width += item_width + 12
        return [row for row in rows if row]

    def _draw_legend(self, left, baseline_y, width):
        y_cursor = baseline_y + (len(self._legend_rows) - 1) * 18
        for row in self._legend_rows:
            cursor_x = left
            for item in row:
                rgba = _rgba_from_hex(item["color"])
                with self.canvas:
                    Color(*rgba)
                    Line(points=[cursor_x, y_cursor + 7, cursor_x + 14, y_cursor + 7], width=2)
                _draw_text(self.canvas, item["name"], cursor_x + 18, y_cursor, font_size=11)
                cursor_x += item["width"] + 12
            y_cursor -= 18

    def _draw_line_series(self, left, bottom, width, height, min_x, max_x, min_y, max_y):
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
            if self.show_points or len(visible_points) <= 40:
                with self.canvas:
                    Color(*rgba)
                    for index in range(0, len(chart_points), 2):
                        Ellipse(pos=(chart_points[index] - 2.4, chart_points[index + 1] - 2.4), size=(4.8, 4.8))

    def _bar_ticks(self, min_x: float, max_x: float) -> list[int]:
        max_index = max((len(item.get("points", [])) for item in self.series), default=0) - 1
        if max_index < 0:
            return []
        start = max(0, int(math.floor(min_x)))
        end = min(max_index, int(math.ceil(max_x)))
        count = end - start + 1
        if count <= 6:
            return list(range(start, end + 1))
        step = max(1, int(math.ceil(count / 5)))
        ticks = list(range(start, end + 1, step))
        if ticks[-1] != end:
            ticks.append(end)
        return ticks

    def _bar_tick_label(self, index: int) -> str:
        if not self.series:
            return str(index)
        points = self.series[0].get("points", [])
        if index < 0 or index >= len(points):
            return str(index + 1)
        x_value = points[index][0]
        return _format_tick(x_value)

    def _draw_bar_series(self, left, bottom, width, height, min_x, max_x, min_y, max_y):
        if not self.series:
            return
        max_count = max((len(item.get("points", [])) for item in self.series), default=0)
        if max_count <= 0:
            return
        visible_start = max(0, int(math.floor(min_x)))
        visible_end = min(max_count - 1, int(math.ceil(max_x)))
        visible_span = max(1.0, max_x - min_x)
        bar_slot_width = width / visible_span
        series_count = max(1, len(self.series))
        bar_width = max(4.0, min(22.0, bar_slot_width * 0.72 / series_count))

        for series_index, item in enumerate(self.series):
            rgba = _rgba_from_hex(item.get("color", "#EC6E00"))
            points = item.get("points", [])
            for index in range(visible_start, visible_end + 1):
                if index >= len(points):
                    continue
                _, y_value = points[index]
                if math.isnan(y_value):
                    continue
                x_center = left + (((index + 0.5) - min_x) / (max_x - min_x)) * width
                x_pos = x_center - (series_count * bar_width) / 2.0 + series_index * bar_width
                y_pos = bottom + ((y_value - min_y) / (max_y - min_y)) * height
                base_y = bottom + ((0.0 - min_y) / (max_y - min_y)) * height
                rect_y = min(base_y, y_pos)
                rect_height = max(1.0, abs(y_pos - base_y))
                with self.canvas:
                    Color(*rgba)
                    Rectangle(pos=(x_pos, rect_y), size=(bar_width - 1.0, rect_height))


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

        legend_rows = len(self.segments)
        legend_height = 18 * legend_rows + 6
        pie_diameter = min(self.width * 0.8, max(72.0, self.height - legend_height - 14))
        center_x = self.center_x
        center_y = self.y + legend_height + pie_diameter / 2 + 10
        rect = (center_x - pie_diameter / 2, center_y - pie_diameter / 2, pie_diameter, pie_diameter)

        start_angle = 0.0
        legend_y = self.y + legend_height - 16
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
            angle_mid = math.radians(start_angle + sweep / 2.0)
            if percentage >= 2.0:
                label_radius = pie_diameter * 0.28
                label_x = center_x + math.cos(angle_mid) * label_radius
                label_y = center_y + math.sin(angle_mid) * label_radius
                text = f"{percentage:.0f}%"
                luminance = rgba[0] * 0.299 + rgba[1] * 0.587 + rgba[2] * 0.114
                text_color = (0.08, 0.08, 0.08, 1.0) if luminance > 0.72 else (1, 1, 1, 1)
                size = _draw_text(self.canvas, text, 0, 0, color=text_color, font_size=12)
                _draw_text(
                    self.canvas,
                    text,
                    label_x - size[0] / 2.0,
                    label_y - size[1] / 2.0,
                    color=text_color,
                    font_size=12,
                )

            with self.canvas:
                Color(*rgba)
                Ellipse(pos=(self.x + 14, legend_y + 3), size=(10, 10))
            legend_text = f"{segment.get('label', 'Dato')}: {int(value)} ({percentage:.0f}%)"
            _draw_text(self.canvas, legend_text, self.x + 30, legend_y, font_size=11)
            legend_y -= 18
            start_angle += sweep

        with self.canvas:
            Color(1, 1, 1, 1)
            inner = pie_diameter * 0.42
            Ellipse(pos=(center_x - inner / 2, center_y - inner / 2), size=(inner, inner))
        total_size = _draw_text(self.canvas, str(int(total)), 0, 0, font_size=14)
        _draw_text(self.canvas, str(int(total)), center_x - total_size[0] / 2.0, center_y - total_size[1] / 2.0, font_size=14)


def _format_tick(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:.0f}"
    if abs(value) >= 100:
        return f"{value:.1f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"
