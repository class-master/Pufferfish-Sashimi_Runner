# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.window import Window

from ..config import WIDTH, HEIGHT
from ..scenes.title import TitleScreen
from ..scenes.play import PlayScreen

class GameScreenManager(ScreenManager):
    pass

class GameApp(App):
    def build(self):
        Window.size = (WIDTH, HEIGHT)
        sm = GameScreenManager(transition=NoTransition())
        sm.add_widget(TitleScreen(name="title"))
        sm.add_widget(PlayScreen(name="play"))
        sm.current = "title"
        return sm
