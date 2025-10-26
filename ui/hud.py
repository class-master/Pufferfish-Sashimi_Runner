# -*- coding: utf-8 -*-
from kivy.uix.label import Label
from kivy.properties import BooleanProperty

class HUD(Label):
    visible = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.markup = True
        self.font_size = "16sp"
        self.halign = "left"
        self.valign = "top"
        self.padding = (8, 8)
        self.text = ""

    def set_info(self, info: dict):
        self.text = (
            "[b]HUD[/b]\\n"
            f"score={int(info.get('score',0))}  hp={info.get('hp',0)}\\n"
            f"speed={info.get('speed',0):.1f}  paused={info.get('paused',False)}"
        )
        self.opacity = 1.0 if self.visible else 0.0
