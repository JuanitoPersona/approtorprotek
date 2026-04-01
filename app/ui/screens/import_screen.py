from __future__ import annotations

import os

from kivy.uix.behaviors import ButtonBehavior
from kivy.effects.scroll import ScrollEffect
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
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


class ClickableFlag(ButtonBehavior, Image):
    pass


class ImportScreen(MDScreen):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller
        self.name = "import"

        root = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        assets_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        logo_path = os.path.join(assets_root, "logo_app_hd.png")
        root.add_widget(Image(source=logo_path, size_hint_y=None, height=dp(88), allow_stretch=True, keep_ratio=True))
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
        language_row = MDGridLayout(cols=4, adaptive_height=True, spacing=dp(10))
        self.language_buttons = {}
        self.language_flags = {}
        for code, image_name in (
            ("es", "lang_es.png"),
            ("en", "lang_en.png"),
            ("fr", "lang_fr.png"),
            ("pt", "lang_pt.png"),
        ):
            box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(6))
            image_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=dp(48))
            flag = ClickableFlag(
                    source=os.path.join(assets_root, image_name),
                    size_hint=(None, None),
                    size=(dp(42), dp(42)),
                    allow_stretch=True,
                    keep_ratio=True,
                )
            flag.bind(on_release=lambda *_args, lang=code: self.app_controller.set_language(lang))
            self.language_flags[code] = flag
            image_anchor.add_widget(flag)
            box.add_widget(image_anchor)
            button = MDFlatButton(text="", on_release=lambda *_args, lang=code: self.app_controller.set_language(lang))
            button.size_hint_x = None
            button.width = dp(96)
            button.pos_hint = {"center_x": 0.5}
            self.language_buttons[code] = button
            box.add_widget(button)
            language_row.add_widget(box)
        self.language_hint_label = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.language_card.body.add_widget(language_row)
        self.language_card.body.add_widget(self.language_hint_label)
        self.body.add_widget(self.language_card)

        self.theme_card = SectionCard("Tema")
        theme_row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(8))
        self.theme_light_button = MDFlatButton(text="", on_release=lambda *_: self.app_controller.set_dark_mode(False))
        self.theme_dark_button = MDFlatButton(text="", on_release=lambda *_: self.app_controller.set_dark_mode(True))
        for button in (self.theme_light_button, self.theme_dark_button):
            button.size_hint_x = None
            button.width = dp(120)
        theme_row.add_widget(self.theme_light_button)
        theme_row.add_widget(self.theme_dark_button)
        self.theme_hint_label = MDLabel(text="", adaptive_height=True, theme_text_color="Secondary")
        self.theme_card.body.add_widget(theme_row)
        self.theme_card.body.add_widget(self.theme_hint_label)
        self.body.add_widget(self.theme_card)

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
        self.body.add_widget(
            Image(
                source=os.path.join(assets_root, "hyperdrive_app.png"),
                size_hint_y=None,
                height=dp(180),
                allow_stretch=True,
                keep_ratio=True,
            )
        )

    def refresh(self):
        state = self.app_controller.state
        self.title_label.text = self.app_controller.tr("import_title")
        self.subtitle_label.text = self.app_controller.tr("import_subtitle")
        self.file_card.title_label.text = self.app_controller.tr("file_card")
        self.file_name_label.text = state.current_file_label if state.current_file_label else self.app_controller.tr("no_file_loaded")
        self.select_button.text = self.app_controller.tr("select_file")
        self.language_card.title_label.text = self.app_controller.tr("language_card")
        self.language_buttons["es"].text = self.app_controller.tr("language_es")
        self.language_buttons["en"].text = self.app_controller.tr("language_en")
        self.language_buttons["fr"].text = self.app_controller.tr("language_fr")
        self.language_buttons["pt"].text = self.app_controller.tr("language_pt")
        self.language_hint_label.text = self.app_controller.tr("language_hint")
        self._style_language_buttons()
        self.theme_card.title_label.text = self.app_controller.tr("theme_card")
        self.theme_light_button.text = self.app_controller.tr("theme_light")
        self.theme_dark_button.text = self.app_controller.tr("theme_dark")
        self.theme_hint_label.text = self.app_controller.tr("theme_hint")
        self._style_theme_buttons()

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
        palette = self.app_controller.palette()
        for code, button in self.language_buttons.items():
            selected = code == active
            button.md_bg_color = (0.925, 0.431, 0.0, 1.0) if selected else palette["inactive_button"]
            button.theme_text_color = "Custom"
            button.text_color = (1, 1, 1, 1) if selected else palette["inactive_text"]
            flag = self.language_flags.get(code)
            if flag is not None:
                flag.opacity = 1.0 if selected else 0.88

    def _style_theme_buttons(self):
        palette = self.app_controller.palette()
        selected_key = "dark" if self.app_controller.dark_mode else "light"
        for key, button in (("light", self.theme_light_button), ("dark", self.theme_dark_button)):
            selected = key == selected_key
            button.md_bg_color = (0.925, 0.431, 0.0, 1.0) if selected else palette["inactive_button"]
            button.theme_text_color = "Custom"
            button.text_color = (1, 1, 1, 1) if selected else palette["inactive_text"]

    def apply_theme(self, palette: dict):
        self.md_bg_color = palette["background"]
        for label in (
            self.title_label,
            self.file_name_label,
            self.validation_label,
        ):
            label.theme_text_color = "Custom"
            label.text_color = palette["text"]
        for label in (
            self.subtitle_label,
            self.language_hint_label,
            self.theme_hint_label,
            self.progress_label,
        ):
            label.theme_text_color = "Custom"
            label.text_color = palette["subtext"]
