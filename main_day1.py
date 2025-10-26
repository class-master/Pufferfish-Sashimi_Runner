# -*- coding: utf-8 -*-
"""
Neon Runner C — Day1（生徒用）Kivy/KivyMD
到達：自動スクロール背景＋ジャンプ（スペース）
TODO：二段ジャンプ／加速レーン／パーティクル
"""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from config import WIDTH, HEIGHT, GROUND_Y, SPEED, JUMP_VEL, GRAVITY, BG

class RunnerGame(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size = (WIDTH, HEIGHT)
        self.scroll = 0.0
        self.x = 120; self.w = 32
        self.ground = GROUND_Y
        self.y = self.ground; self.h = 32
        self.vy = 0.0; self.on_ground = True
        self.keys=set()
        Window.bind(on_key_down=self._kd, on_key_up=self._ku)
        self.hint = Label(text="Space: ジャンプ / TODO: 二段ジャンプなど", pos=(12, HEIGHT-28))
        self.add_widget(self.hint)
        Clock.schedule_interval(self.update, 1/60)

    def _kd(self,win,key,*a):
        self.keys.add(key)
        if key == 32 and self.on_ground:  # Space
            self.vy = JUMP_VEL; self.on_ground = False
        return True

    def _ku(self,win,key,*a):
        self.keys.discard(key); return True

    def update(self, dt):
        # 背景スクロール（パララックス擬似）
        self.scroll += SPEED

        # 重力とジャンプ
        if not self.on_ground:
            self.vy -= GRAVITY
            self.y += self.vy
            if self.y <= self.ground:
                self.y = self.ground; self.vy = 0; self.on_ground = True

        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # 背景
            Color(*BG); Rectangle(pos=self.pos, size=self.size)
            # パララックス風ライン
            Color(0.10,0.13,0.2,1)
            for i in range(12):
                x = - (self.scroll*0.5 % 160) + i*160
                Rectangle(pos=(x, 360), size=(140, 2))
            Color(0.14,0.18,0.28,1)
            for i in range(12):
                x = - (self.scroll*0.8 % 220) + i*220
                Rectangle(pos=(x, 260), size=(180, 3))
            # 地面
            Color(0.25,0.8,0.9,1); Rectangle(pos=(0, self.ground-6), size=(self.width, 6))
            # ランナー
            Color(0.95,0.2,0.6,1); Rectangle(pos=(self.x, self.y), size=(self.w, self.h))

class NeonRunnerDay1(App):
    def build(self):
        return RunnerGame()

if __name__ == "__main__":
    NeonRunnerDay1().run()
