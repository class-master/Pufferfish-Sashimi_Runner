# -*- coding: utf-8 -*-
"""
[A] Controller: レーン移動/ジャンプを担当
- move_left/right: レーン番号 0..LANES-1 でスナップ
- try_jump: 地上判定（GROUND_Y）に近いときのみ vy に初速
- STEP: "コヨーテタイム"（着地直後一定時間ジャンプ許可）を追加してみよう（任意）
"""
from dataclasses import dataclass
from typing import Tuple
from time import monotonic

from src import config

@dataclass
class Player:
    lane: int = 1
    x: float = config.lane_x(1)
    y: float = config.PLAYER_GROUND_Y
    vy: float = 0.0
    w: float = config.PLAYER_W
    h: float = config.PLAYER_H
    hp: int = config.START_HP
    inv_until: float = 0.0

    def rect(self) -> Tuple[float, float, float, float]:
        half_w, half_h = self.w*0.5, self.h*0.5
        return (self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h)

    # --- レーン操作 ---
    def move_left(self):
        if self.lane > 0:
            self.lane -= 1
            self.x = config.lane_x(self.lane)

    def move_right(self):
        if self.lane < config.LANES - 1:
            self.lane += 1
            self.x = config.lane_x(self.lane)

    # --- ジャンプ ---
    def is_grounded(self) -> bool:
        return self.y <= config.PLAYER_GROUND_Y + 1.0

    def try_jump(self):
        # STEP: コヨーテタイムを導入するなら、最後に地面に居た時刻を覚え、
        # その差分がしきい値以内ならジャンプ許可にする。
        if self.is_grounded():
            self.vy = config.JUMP_VELOCITY

    # --- 更新 ---
    def update(self, dt: float):
        self.vy -= config.GRAVITY * dt
        self.y += self.vy * dt
        if self.y < config.PLAYER_GROUND_Y:
            self.y = config.PLAYER_GROUND_Y
            self.vy = 0.0

    # --- ダメージ処理 ---
    def can_damage(self, now_s: float) -> bool:
        return now_s >= self.inv_until and self.hp > 0

    def on_hit(self, now_s: float):
        if self.can_damage(now_s):
            self.hp -= 1
            self.inv_until = now_s + config.INVULN_TIME
