from __future__ import annotations

import os

from kivy.metrics import dp
from kivy.uix.screenmanager import FadeTransition, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel

from ..android_file_picker import AndroidCsvPicker, is_android_runtime
from ..mobile_state import MobileAppState
from .screens.condition_monitoring_screen import ConditionMonitoringScreen
from .screens.historical_screen import HistoricalScreen
from .screens.import_screen import ImportScreen
from .screens.viewer_screen import ViewerScreen
from .theme import APP_THEME


class RotorProtekMobileApp(MDApp):
    def build(self):
        self.title = "RotorProtek"
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        self.state = MobileAppState()
        self.android_picker = None

        self.file_manager = MDFileManager(exit_manager=self.close_file_manager, select_path=self._select_file_from_desktop, preview=False)
        if is_android_runtime():
            self.android_picker = AndroidCsvPicker(
                on_success=self._select_file_from_android,
                on_cancel=self._handle_picker_cancel,
                on_error=self._handle_picker_error,
            )

        root = MDBoxLayout(orientation="vertical", md_bg_color=APP_THEME["background"])
        header = MDBoxLayout(orientation="vertical", adaptive_height=True, padding=dp(16), spacing=dp(8))
        header.add_widget(MDLabel(text="RotorProtek", bold=True, font_style="H5", adaptive_height=True))
        self.file_label = MDLabel(text="Sin CSV cargado", adaptive_height=True, theme_text_color="Secondary")
        header.add_widget(self.file_label)

        nav_scroll = ScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height=dp(44),
            bar_width=0,
        )
        nav = MDBoxLayout(orientation="horizontal", adaptive_width=True, spacing=dp(8))
        self.import_button = MDRaisedButton(text="CSV", on_release=lambda *_: self.show_screen("import"))
        self.viewer_button = MDFlatButton(text="Arranque", on_release=lambda *_: self.show_screen("viewer"))
        self.cm_button = MDFlatButton(text="CM", on_release=lambda *_: self.show_screen("condition_monitoring"))
        self.history_button = MDFlatButton(text="Historico", on_release=lambda *_: self.show_screen("historical"))
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
        for screen in (self.import_screen, self.viewer_screen, self.cm_screen, self.historical_screen):
            self.screen_manager.add_widget(screen)
        root.add_widget(self.screen_manager)

        self.refresh_ui()
        return root

    def open_file_manager(self):
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
        if not candidate_name.lower().endswith(".csv"):
            self.state.validation_messages = ["El archivo seleccionado no es un CSV."]
            self.refresh_ui()
            self.show_screen("import")
            return

        ok, message = self.state.load_csv(path, display_name=candidate_name)
        extra_messages = [msg for msg in self.state.validation_messages if msg != message]
        self.state.validation_messages = [message] + extra_messages
        self.refresh_ui()
        self.show_screen("viewer" if ok else "import")

    def _handle_picker_cancel(self):
        self.state.validation_messages = ["Seleccion de archivo cancelada por el usuario."]
        self.refresh_ui()
        self.show_screen("import")

    def _handle_picker_error(self, message: str):
        self.state.validation_messages = [message]
        self.refresh_ui()
        self.show_screen("import")

    def show_screen(self, name: str):
        if name == "viewer" and not self.state.has_dataset:
            return
        if name in ("condition_monitoring", "historical") and not self.state.is_multi:
            return
        self.screen_manager.current = name

    def refresh_ui(self):
        self.file_label.text = self.state.current_file_label if self.state.current_file_label else "Sin CSV cargado"
        self._set_nav_visibility(self.viewer_button, self.state.has_dataset)
        self._set_nav_visibility(self.cm_button, self.state.is_multi)
        self._set_nav_visibility(self.history_button, self.state.is_multi)
        self.import_screen.refresh()
        self.viewer_screen.refresh()
        self.cm_screen.refresh()
        self.historical_screen.refresh()

    def _set_nav_visibility(self, widget, visible: bool):
        widget.disabled = not visible
        widget.opacity = 1 if visible else 0
        widget.width = dp(88) if visible else 0
