# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Tuple
from src import config

@dataclass
class Obstacle:
    lane: int
    x: float
    y: float
    w: float = config.PLAYER_W
    h: float = config.PLAYER_H
    alive: bool = True

    def rect(self) -> Tuple[float, float, float, float]:
        hw, hh = self.w*0.5, self.h*0.5
        return (self.x - hw, self.y - hh, self.x + hw, self.y + hh)

    def update(self, dt: float, speed: float):
        self.y -= speed * dt
        if self.y < -self.h:
            self.alive = False
