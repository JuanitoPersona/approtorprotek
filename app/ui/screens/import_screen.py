from __future__ import annotations

import os

from kivy.effects.scroll import ScrollEffect
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
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
        root.add_widget(MDLabel(text="Carga de archivo", bold=True, font_style="H5", adaptive_height=True))
        root.add_widget(
            MDLabel(
                text="Importa un CSV o XLSX de RotorProtek desde el dispositivo y valida su estructura antes de abrir las pantallas de analisis.",
                theme_text_color="Secondary",
                adaptive_height=True,
            )
        )

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
        self.file_card.body.add_widget(
            MDRaisedButton(
                text="Seleccionar CSV o XLSX",
                pos_hint={"center_x": 0.5},
                on_release=lambda *_: self.app_controller.open_file_manager(),
            )
        )
        self.body.add_widget(self.file_card)

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
        self.file_name_label.text = state.current_file_label if state.current_file_label else "Ningun archivo cargado"

        self.summary_grid.clear_widgets()
        self.summary_grid.add_widget(MetricCard("Estado", "Listo" if state.last_load_ok else "Pendiente"))
        if state.has_dataset:
            total = len(state.records)
            mode = "Multi" if state.is_multi else "Unico"
            self.summary_grid.add_widget(MetricCard("Arranques", str(total)))
            self.summary_grid.add_widget(MetricCard("Modo", mode))
        else:
            self.summary_grid.add_widget(MetricCard("Arranques", "0"))
            self.summary_grid.add_widget(MetricCard("Modo", "Sin datos"))

        if state.validation_messages:
            self.validation_label.text = "\n".join(f"- {message}" for message in state.validation_messages)
        elif state.has_dataset:
            self.validation_label.text = "Archivo valido y listo para usar."
        else:
            self.validation_label.text = "Selecciona un CSV o XLSX para comenzar."

        loading = getattr(self.app_controller, "_loading_csv", False)
        self.progress_bar.opacity = 1 if loading else 0
        self.progress_label.opacity = 1 if loading else 0
        self.progress_bar.value = state.load_progress if loading else 0
        self.progress_label.text = f"Carga en progreso: {state.load_progress}%" if loading else ""
