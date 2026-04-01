from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel


class SectionCard(MDCard):
    def __init__(self, title: str, **kwargs):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(10), radius=[18], **kwargs)
        self.size_hint_y = None
        self.adaptive_height = True
        self.elevation = 1
        self.md_bg_color = (1, 1, 1, 1)
        self.title_label = MDLabel(text=title, bold=True, theme_text_color="Primary", adaptive_height=True)
        self.body = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(10))
        self.add_widget(self.title_label)
        self.add_widget(self.body)

    def apply_theme(self, palette: dict):
        self.md_bg_color = palette["panel"]


class MetricCard(MDCard):
    def __init__(self, label: str, value: str, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(6), radius=[16], **kwargs)
        self.size_hint_y = None
        self.adaptive_height = True
        self.minimum_height = dp(96)
        self.elevation = 1
        self.md_bg_color = (0.98, 0.98, 0.98, 1)
        self.label_widget = MDLabel(text=label, theme_text_color="Secondary", adaptive_height=True)
        self.value_widget = MDLabel(text=str(value), bold=True, adaptive_height=True)
        self.add_widget(self.label_widget)
        self.add_widget(self.value_widget)

    def apply_theme(self, palette: dict):
        self.md_bg_color = palette["panel_soft"]


class EmptyState(MDCard):
    def __init__(self, text: str, **kwargs):
        super().__init__(orientation="vertical", padding=dp(18), radius=[16], **kwargs)
        self.size_hint_y = None
        self.adaptive_height = True
        self.md_bg_color = (0.97, 0.97, 0.97, 1)
        self.text_widget = MDLabel(text=text, halign="center", theme_text_color="Secondary", adaptive_height=True)
        self.add_widget(self.text_widget)

    def apply_theme(self, palette: dict):
        self.md_bg_color = palette["panel_muted"]
