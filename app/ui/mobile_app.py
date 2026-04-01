from __future__ import annotations

import os
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.screenmanager import FadeTransition, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel

from ..android_share import export_widget_png, is_android_runtime as is_android_share_runtime, share_png_file
from ..android_file_picker import AndroidCsvPicker, is_android_runtime
from ..mobile_state import MobileAppState
from .screens.condition_monitoring_screen import ConditionMonitoringScreen
from .screens.fullscreen_chart_screen import FullscreenChartScreen
from .screens.historical_screen import HistoricalScreen
from .screens.import_screen import ImportScreen
from .screens.viewer_screen import ViewerScreen
from .i18n import tr
from .theme import get_theme


class ClickableImage(ButtonBehavior, Image):
    pass


class RotorProtekMobileApp(MDApp):
    def build(self):
        self.language = "es"
        self.dark_mode = False
        self.title = self.tr("app_title")
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        self.state = MobileAppState()
        self.android_picker = None
        self._loading_csv = False
        self._last_progress_percent = -1
        self._previous_screen = "import"
        self._header_visible = True

        self.file_manager = MDFileManager(exit_manager=self.close_file_manager, select_path=self._select_file_from_desktop, preview=False)
        if is_android_runtime():
            self.android_picker = AndroidCsvPicker(
                on_success=self._select_file_from_android,
                on_cancel=self._handle_picker_cancel,
                on_error=self._handle_picker_error,
            )

        palette = self.palette()
        root = MDBoxLayout(orientation="vertical", md_bg_color=palette["background"])
        self.root_layout = root
        header = MDBoxLayout(orientation="vertical", adaptive_height=True, padding=dp(16), spacing=dp(8))
        self.header = header
        self.app_title_label = MDLabel(text=self.tr("app_title"), bold=True, font_style="H5", adaptive_height=True)
        header.add_widget(self.app_title_label)
        self.file_label = MDLabel(text=self.tr("no_file_loaded"), adaptive_height=True, theme_text_color="Secondary")
        header.add_widget(self.file_label)

        nav_scroll = ScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height=dp(44),
            bar_width=0,
        )
        nav = MDBoxLayout(orientation="horizontal", adaptive_width=True, spacing=dp(8))
        self.import_button = MDRaisedButton(text=self.tr("nav_file"), on_release=lambda *_: self.show_screen("import"))
        self.viewer_button = MDRaisedButton(text=self.tr("nav_viewer"), on_release=lambda *_: self.show_screen("viewer"))
        self.cm_button = MDRaisedButton(text=self.tr("nav_cm"), on_release=lambda *_: self.show_screen("condition_monitoring"))
        self.history_button = MDRaisedButton(text=self.tr("nav_history"), on_release=lambda *_: self.show_screen("historical"))
        for button in (self.import_button, self.viewer_button, self.cm_button, self.history_button):
            button.size_hint_x = None
            button.width = dp(88)
            nav.add_widget(button)
        nav_scroll.add_widget(nav)
        header.add_widget(nav_scroll)
        root.add_widget(header)

        self.screen_manager = ScreenManager(transition=FadeTransition())
        self.import_screen = ImportScreen(self)
        self.viewer_screen = ViewerScreen(self)
        self.cm_screen = ConditionMonitoringScreen(self)
        self.historical_screen = HistoricalScreen(self)
        self.fullscreen_chart_screen = FullscreenChartScreen(self)
        for screen in (self.import_screen, self.viewer_screen, self.cm_screen, self.historical_screen, self.fullscreen_chart_screen):
            self.screen_manager.add_widget(screen)
        root.add_widget(self.screen_manager)

        self.refresh_ui()
        self._header_visible = False
        self.set_header_visible(True)
        return root

    def open_file_manager(self):
        if self._loading_csv:
            self.state.validation_messages = ["Espera a que termine la carga actual del archivo."]
            self.refresh_ui()
            self.show_screen("import")
            return
        if self.android_picker is not None:
            self.state.validation_messages = ["Abriendo selector Android..."]
            self.refresh_ui()
            self.android_picker.open()
            return

        start_path = "/storage/emulated/0" if os.path.exists("/storage/emulated/0") else os.getcwd()
        self.file_manager.show(start_path)

    def close_file_manager(self, *_args):
        self.file_manager.close()

    def _select_file_from_desktop(self, path: str):
        self.close_file_manager()
        self.select_file_path(path)

    def _select_file_from_android(self, local_path: str, display_name: str):
        self.select_file_path(local_path, display_name=display_name)

    def select_file_path(self, path: str, display_name: str | None = None):
        candidate_name = (display_name or os.path.basename(path or "")).strip()
        if not candidate_name.lower().endswith((".csv", ".xlsx")):
            self.state.validation_messages = ["El archivo seleccionado no es compatible. Usa CSV o XLSX."]
            self.refresh_ui()
            self.show_screen("import")
            return

        self._loading_csv = True
        self._last_progress_percent = -1
        self.state.current_file_label = candidate_name
        self.state.load_progress = 0
        self.state.validation_messages = [f"Cargando {candidate_name}..."]
        self.refresh_ui()
        self.show_screen("import")
        Thread(
            target=self._load_csv_worker,
            args=(path, candidate_name),
            daemon=True,
        ).start()

    def _load_csv_worker(self, path: str, candidate_name: str):
        ok, message = self.state.load_csv(
            path,
            display_name=candidate_name,
            progress_callback=self._report_csv_progress,
        )
        Clock.schedule_once(lambda *_: self._finish_csv_load(ok, message), 0)

    def _report_csv_progress(self, percent: int, message: str):
        if percent == self._last_progress_percent and message in self.state.validation_messages:
            return
        self._last_progress_percent = percent
        Clock.schedule_once(lambda *_: self._apply_csv_progress(percent, message), 0)

    def _apply_csv_progress(self, percent: int, message: str):
        if not self._loading_csv:
            return
        self.state.load_progress = percent
        self.state.validation_messages = [f"{message} ({percent}%)"]
        self.refresh_ui()

    def _finish_csv_load(self, ok: bool, message: str):
        self._loading_csv = False
        self._last_progress_percent = -1
        extra_messages = [msg for msg in self.state.validation_messages if msg != message and not str(msg).startswith("Cargando ")]
        self.state.validation_messages = [message] + extra_messages
        self.refresh_ui()
        self.show_screen("viewer" if ok else "import")

    def _handle_picker_cancel(self):
        self._loading_csv = False
        self.state.validation_messages = ["Seleccion de archivo cancelada por el usuario."]
        self.refresh_ui()
        self.show_screen("import")

    def _handle_picker_error(self, message: str):
        self._loading_csv = False
        self.state.validation_messages = [message]
        self.refresh_ui()
        self.show_screen("import")

    def show_screen(self, name: str):
        if name == "viewer" and not self.state.has_dataset:
            return
        if name in ("condition_monitoring", "historical") and not self.state.is_multi:
            return
        if name != "fullscreen_chart":
            self._previous_screen = name
        self.screen_manager.current = name
        self.set_header_visible(name != "fullscreen_chart")
        self._update_nav_active(name)
        self._refresh_active_screen()
        self._apply_theme()

    def open_fullscreen_chart(
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
        try:
            self.fullscreen_chart_screen.apply_chart(
                title=title,
                subtitle=subtitle,
                series=series,
                x_axis_label=x_axis_label,
                y_axis_label=y_axis_label,
                chart_mode=chart_mode,
                show_legend=show_legend,
                show_points=show_points,
                x_tick_labels=x_tick_labels or [],
                allow_point_deletion=allow_point_deletion,
                footer=footer,
            )
            self.show_screen("fullscreen_chart")
        except Exception as exc:
            self.state.validation_messages = [f"No se pudo abrir la grafica a pantalla completa: {exc}"]
            self.refresh_ui()

    def close_fullscreen_chart(self):
        target = self._previous_screen if self._previous_screen in {"import", "viewer", "condition_monitoring", "historical"} else "viewer"
        self.screen_manager.current = target
        self.set_header_visible(True)
        self._refresh_active_screen()
        self._apply_theme()

    def set_header_visible(self, visible: bool):
        if not hasattr(self, "header"):
            return
        if self._header_visible == visible:
            return
        self._header_visible = visible
        self.header.opacity = 1 if visible else 0
        self.header.height = self.header.minimum_height if visible else 0

    def handle_screen_scroll(self, scroll_y: float):
        if getattr(self, "screen_manager", None) is None:
            return
        current = self.screen_manager.current
        if current == "fullscreen_chart":
            self.set_header_visible(False)
            return
        if current not in {"viewer", "condition_monitoring", "historical"}:
            self.set_header_visible(True)
            return
        if self._header_visible and scroll_y < 0.96:
            self.set_header_visible(False)
        elif not self._header_visible and scroll_y > 0.992:
            self.set_header_visible(True)

    def refresh_ui(self):
        self.title = self.tr("app_title")
        self.app_title_label.text = self.tr("app_title")
        self.file_label.text = self.state.current_file_label if self.state.current_file_label else self.tr("no_file_loaded")
        self.import_button.text = self.tr("nav_file")
        self.viewer_button.text = self.tr("nav_viewer")
        self.cm_button.text = self.tr("nav_cm")
        self.history_button.text = self.tr("nav_history")
        self._set_nav_visibility(self.viewer_button, self.state.has_dataset)
        self._set_nav_visibility(self.cm_button, self.state.is_multi)
        self._set_nav_visibility(self.history_button, self.state.is_multi)
        self._update_nav_active(self.screen_manager.current if getattr(self, "screen_manager", None) else "import")
        self.import_screen.refresh()
        self._refresh_active_screen()
        self._apply_theme()

    def _set_nav_visibility(self, widget, visible: bool):
        widget.disabled = not visible
        widget.opacity = 1 if visible else 0
        widget.width = dp(88) if visible else 0

    def _update_nav_active(self, screen_name: str):
        if screen_name == "fullscreen_chart":
            screen_name = self._previous_screen
        active_map = {
            "import": self.import_button,
            "viewer": self.viewer_button,
            "condition_monitoring": self.cm_button,
            "historical": self.history_button,
        }
        for screen, button in active_map.items():
            active = screen == screen_name
            palette = self.palette()
            button.md_bg_color = (0.925, 0.431, 0.0, 1.0) if active else palette["inactive_button"]
            button.theme_text_color = "Custom"
            button.text_color = (1, 1, 1, 1) if active else palette["inactive_text"]

    def tr(self, key: str, **kwargs) -> str:
        return tr(self.language, key, **kwargs)

    def tr_metric(self, label: str) -> str:
        from .i18n import tr_metric

        return tr_metric(self.language, label)

    def palette(self) -> dict:
        return get_theme(self.dark_mode)

    def set_language(self, language: str):
        if language not in {"es", "en", "fr", "pt"} or language == self.language:
            return
        self.language = language
        self.refresh_ui()

    def set_dark_mode(self, dark_mode: bool):
        dark_mode = bool(dark_mode)
        if dark_mode == self.dark_mode:
            return
        self.dark_mode = dark_mode
        self.refresh_ui()

    def toggle_dark_mode(self):
        self.set_dark_mode(not self.dark_mode)

    def share_chart_widget(self, widget, title: str):
        try:
            file_path = export_widget_png(widget, title)
            ok, message = share_png_file(file_path, chooser_title=self.tr("share"))
            if ok:
                self.state.validation_messages = [self.tr("share_sent")]
            elif is_android_share_runtime():
                self.state.validation_messages = [self.tr("share_error", error=message)]
            else:
                self.state.validation_messages = [self.tr("share_saved", path=message)]
        except Exception as exc:
            self.state.validation_messages = [self.tr("share_error", error=str(exc))]
        self.refresh_ui()

    def _refresh_active_screen(self):
        current = self.screen_manager.current if getattr(self, "screen_manager", None) else "import"
        if current == "viewer":
            self.viewer_screen.refresh()
        elif current == "condition_monitoring":
            self.cm_screen.refresh()
        elif current == "historical":
            self.historical_screen.refresh()
        elif current == "fullscreen_chart":
            pass
        else:
            self.import_screen.refresh()

    def _apply_theme(self):
        palette = self.palette()
        self.theme_cls.theme_style = "Dark" if self.dark_mode else "Light"
        if hasattr(self, "root_layout"):
            self.root_layout.md_bg_color = palette["background"]
        if hasattr(self, "screen_manager"):
            self._apply_widget_theme(self.screen_manager, palette)
        if hasattr(self, "header"):
            self._apply_widget_theme(self.header, palette)

    def _apply_widget_theme(self, widget, palette: dict):
        if hasattr(widget, "apply_theme"):
            widget.apply_theme(palette)
        if hasattr(widget, "dark_mode"):
            try:
                widget.dark_mode = self.dark_mode
            except Exception:
                pass
        for child in getattr(widget, "children", []):
            self._apply_widget_theme(child, palette)
