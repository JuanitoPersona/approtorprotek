from __future__ import annotations

import os

from kivy.effects.scroll import ScrollEffect
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from ..widgets.cards import MetricCard, SectionCard


class ImportScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "import"

        root = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logo_app.png")
        root.add_widget(Image(source=logo_path, size_hint_y=None, height=dp(72), allow_stretch=True, keep_ratio=True))
        self.title_label = MDLabel(text="", bold=True, font_style="H5", adaptive_height=True)
        self.subtitle_label = MDLabel(text="", theme_text_color="Secondary", adaptive_height=True)
        root.add_widget(self.title_label)
        root.add_widget(self.subtitle_label)

        scroll = ScrollView(do_scroll_x=False, effect_cls=ScrollEffect)
        self.scroll = scroll
        self.scroll.bind(scroll_y=lambda *_args: self.app_controller.handle_screen_scroll(self.scroll.scroll_y))
        self.body = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(12), padding=(0, dp(8), 0, dp(24)))
        scroll.add_widget(self.body)
        root.add_widget(scroll)
        self.add_widget(root)

        self.file_card = SectionCard("Archivo")
        self.file_name_label = MDLabel(text="Ningun archivo cargado", adaptive_height=True)
        self.file_card.body.add_widget(self.file_name_label)
        self.select_button = MDRaisedButton(text="", pos_hint={"center_x": 0.5}, on_release=lambda *_: self.app_controller.open_file_manager())
        self.file_card.body.add_widget(self.select_button)
        self.body.add_widget(self.file_card)

        self.language_card = SectionCard("Idioma")
        language_row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
        self.lang_es_button = MDFlatButton(text="", on_release=lambda *_: self.app_controller.set_language("es"))
        self.lang_en_button = MDFlatButton(text="", on_release=lambda *_: self.app_controller.set_language("en"))
        language_row.add_widget(self.lang_es_button)
        language_row.add_widget(self.lang_en_button)
        self.language_hint_label = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.language_card.body.add_widget(language_row)
        self.language_card.body.add_widget(self.language_hint_label)
        self.body.add_widget(self.language_card)

        self.summary_card = SectionCard("Resumen")
        self.summary_grid = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(10), row_default_height=dp(96), row_force_default=True)
        self.summary_card.body.add_widget(self.summary_grid)
        self.body.add_widget(self.summary_card)

        self.validation_card = SectionCard("Validacion")
        self.validation_label = MDLabel(text="Selecciona un CSV o XLSX para comenzar.", adaptive_height=True)
        self.progress_label = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(12))
        self.validation_card.body.add_widget(self.validation_label)
        self.validation_card.body.add_widget(self.progress_label)
        self.validation_card.body.add_widget(self.progress_bar)
        self.body.add_widget(self.validation_card)

    def refresh(self):
        state = self.app_controller.state
        self.title_label.text = self.app_controller.tr("import_title")
        self.subtitle_label.text = self.app_controller.tr("import_subtitle")
        self.file_card.title_label.text = self.app_controller.tr("file_card")
        self.file_name_label.text = state.current_file_label if state.current_file_label else self.app_controller.tr("no_file_loaded")
        self.select_button.text = self.app_controller.tr("select_file")
        self.language_card.title_label.text = self.app_controller.tr("language_card")
        self.lang_es_button.text = self.app_controller.tr("language_es")
        self.lang_en_button.text = self.app_controller.tr("language_en")
        self.language_hint_label.text = self.app_controller.tr("language_hint")
        self._style_language_buttons()

        self.summary_grid.clear_widgets()
        self.summary_card.title_label.text = self.app_controller.tr("summary_card")
        self.summary_grid.add_widget(MetricCard(self.app_controller.tr("status_label"), self.app_controller.tr("status_ready") if state.last_load_ok else self.app_controller.tr("status_pending")))
        if state.has_dataset:
            total = len(state.records)
            mode = self.app_controller.tr("mode_multi") if state.is_multi else self.app_controller.tr("mode_single")
            self.summary_grid.add_widget(MetricCard(self.app_controller.tr("starts"), str(total)))
            self.summary_grid.add_widget(MetricCard(self.app_controller.tr("mode"), mode))
        else:
            self.summary_grid.add_widget(MetricCard(self.app_controller.tr("starts"), "0"))
            self.summary_grid.add_widget(MetricCard(self.app_controller.tr("mode"), self.app_controller.tr("mode_empty")))

        self.validation_card.title_label.text = self.app_controller.tr("validation_card")
        if state.validation_messages:
            self.validation_label.text = "\n".join(f"- {message}" for message in state.validation_messages)
        elif state.has_dataset:
            self.validation_label.text = self.app_controller.tr("validation_ok")
        else:
            self.validation_label.text = self.app_controller.tr("validation_default")

        loading = getattr(self.app_controller, "_loading_csv", False)
        self.progress_bar.opacity = 1 if loading else 0
        self.progress_label.opacity = 1 if loading else 0
        self.progress_bar.value = state.load_progress if loading else 0
        self.progress_label.text = self.app_controller.tr("progress_loading", percent=state.load_progress) if loading else ""

    def _style_language_buttons(self):
        active = self.app_controller.language
        for code, button in (("es", self.lang_es_button), ("en", self.lang_en_button)):
            selected = code == active
            button.md_bg_color = (0.925, 0.431, 0.0, 1.0) if selected else (0.91, 0.91, 0.91, 1.0)
            button.theme_text_color = "Custom"
            button.text_color = (1, 1, 1, 1) if selected else (0.25, 0.25, 0.25, 1)
