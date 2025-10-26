# -*- coding: utf-8 -*-
"""
[E] Title: Enter→Play / Esc→Quit
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock

class TitleScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(Label(text="[b]NeonRunner[/b]", markup=True, font_size="28sp"))
        layout.add_widget(Label(text="Press [b]Enter[/b] → Play", markup=True))
        layout.add_widget(Label(text="Press [b]Esc[/b] → Quit", markup=True))
        self.add_widget(layout)

        self._kb = None
        Clock.schedule_once(self._bind, 0)

    def _bind(self, *_):
        self._kb = Window.request_keyboard(self._kb_closed, self)
        if self._kb:
            self._kb.bind(on_key_down=self._on_key_down)

    def _kb_closed(self, *_):
        if self._kb:
            self._kb.unbind(on_key_down=self._on_key_down)
            self._kb = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        _, s = keycode
        if s in ("enter", "numpadenter"):
            self.manager.current = "play"
            return True
        if s == "escape":
            from kivy.app import App
            App.get_running_app().stop()
            return True
        return False
