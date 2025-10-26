# -*- coding: utf-8 -*-
"""
[C] Spawner: 生成間隔を設計する
- periodic+jitter（既定）/ poisson（STEP）/ speed連動（STEP）
"""
import random, math
from typing import List
from src import config
from src.game.obstacle import Obstacle

class Spawner:
    def __init__(self):
        self.timer = 0.0
        self.next_interval = self._next_interval()

    def _poisson(self, lam: float) -> float:
        # Poisson 乱数の待ち時間（指数分布）: -ln(1-U)/lam
        u = 1.0 - random.random()
        return -math.log(u) / lam

    def _next_interval(self) -> float:
        if config.SPAWN_MODE == "poisson":
            iv = self._poisson(lam=1.0/max(0.001, config.SPAWN_BASE_INTERVAL))
        else:
            jitter = random.uniform(-config.SPAWN_RANDOM_JITTER, config.SPAWN_RANDOM_JITTER)
            iv = config.SPAWN_BASE_INTERVAL + jitter
        return max(config.SPAWN_MIN_INTERVAL, iv)

    def update(self, dt: float, obstacles: List[Obstacle], speed: float):
        # STEP: speed 連動 → interval *= BASE_SPEED / speed を試してみよう
        self.timer += dt
        if self.timer >= self.next_interval:
            self.timer = 0.0
            self.next_interval = self._next_interval()

            # 1～2個を出す（揺らぎ）
            count = 1 if random.random() < 0.7 else 2
            lanes = list(range(config.LANES))
            random.shuffle(lanes)
            for i in range(count):
                lane = lanes[i % config.LANES]
                x = config.lane_x(lane)
                y = config.HEIGHT + config.PLAYER_H
                obstacles.append(Obstacle(lane=lane, x=x, y=y))
