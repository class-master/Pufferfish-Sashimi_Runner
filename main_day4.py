# -*- coding: utf-8 -*-
"""
Neon Runner C — Day4（生徒用）Kivy/KivyMD
到達：ジャンプ／着地／GameOverのエフェクト＋Rキーでリスタート
TODO：サウンド追加／タイトル画面／カウントダウン演出
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
        self.base_speed = SPEED
        self.time = 0.0
        self.x = 120; self.w = 32
        self.ground = GROUND_Y
        self.y = self.ground; self.h = 32
        self.vy = 0.0; self.on_ground = True
        self.obstacles = []  # list of (x,y,w,h)
        self.score = 0; self.gameover = False
        self.keys=set()
        Window.bind(on_key_down=self._kd, on_key_up=self._ku)
        self.hud = Label(text="Space: ジャンプ / 障害物を避けてスコアUP", pos=(12, HEIGHT-28))
        self.add_widget(self.hud)
        Clock.schedule_interval(self.update, 1/60)

    def _kd(self,win,key,*a):
        self.keys.add(key)
        if key == 32 and self.on_ground and not self.gameover:
            self.vy = JUMP_VEL; self.on_ground = False
        return True

    def _ku(self,win,key,*a):
        self.keys.discard(key); return True

    def _speed(self):
        # 時間で少しずつ加速（発展でカーブ変更可）
        return self.base_speed + min(6.0, self.time*0.05)

    def spawn_obstacle(self):
        import random
        gap = random.choice([260, 320, 380])
        last_x = max([o[0] for o in self.obstacles], default=self.width + 100)
        x = max(self.width + 60, last_x + gap)
        w = random.choice([26, 32, 40])
        h = random.choice([26, 32, 44])
        self.obstacles.append([x, self.ground, w, h])

    def aabb(self, ax, ay, aw, ah, bx, by, bw, bh):
        return not (ax+aw <= bx or bx+bw <= ax or ay+ah <= by or by+bh <= ay)

    def update(self, dt):
        if self.gameover:
            self.draw(); return
        self.time += 1.0
        spd = self._speed()
        self.scroll += spd

        # 重力・ジャンプ
        if not self.on_ground:
            self.vy -= GRAVITY
            self.y += self.vy
            if self.y <= self.ground:
                self.y = self.ground; self.vy = 0; self.on_ground = True

        # 障害物生成／更新
        if not self.obstacles or (self.obstacles and self.obstacles[-1][0] < self.width):
            # ランダムに生成
            if random.random() < 0.04:
                self.spawn_obstacle()
        for o in self.obstacles:
            o[0] -= spd
        self.obstacles = [o for o in self.obstacles if o[0] + o[2] > -40]

        # 当たり判定／スコア
        for (ox,oy,ow,oh) in self.obstacles:
            if self.aabb(self.x,self.y,self.w,self.h, ox,oy,ow,oh):
                self.gameover = True
        if not self.gameover:
            self.score += int(spd)

        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # 背景
            Color(*BG); Rectangle(pos=self.pos, size=self.size)
            # 地面
            Color(0.25,0.8,0.9,1); Rectangle(pos=(0, self.ground-6), size=(self.width, 6))
            # 障害物
            Color(1.0,0.45,0.2,1)
            for (ox,oy,ow,oh) in self.obstacles:
                Rectangle(pos=(ox,oy), size=(ow,oh))
            # ランナー
            Color(0.95,0.2,0.6,1); Rectangle(pos=(self.x, self.y), size=(self.w, self.h))
        self.hud.text = f"Score: {self.score}" + ("  — GAME OVER" if self.gameover else "")

class NeonRunnerDay2(App):
    def build(self):
        return RunnerGame()

if __name__ == "__main__":
    NeonRunnerDay2().run()
