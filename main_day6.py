# -*- coding: utf-8 -*-
"""
Pufferfish-Sashimi Runner — Day6
目的：
- 実行場所（カレントディレクトリ）に依存しない「正しいパス参照」に矯正する
- Day7以降の機能追加でパス地獄にならない土台を作る

今日の成功条件：
- repo直下/assets/neon_banner.png が表示できる
- repo直下/bgm.ogg が再生できる（無い場合は require_bgm=False にしてOK）
"""

from kivy.app import App
from kivy.uix.image import Image
from kivy.core.audio import SoundLoader

from utils.paths import sanity_check, asset_path, repo_path


class Day6App(App):
    def build(self):
        # 1) 起動直後に「壊れない土台」を検査（原因が分かりやすいメッセージで落ちる）
        sanity_check(require_bgm=True)

        # 2) 画像（repo直下/assets/neon_banner.png）
        banner = Image(source=asset_path("neon_banner.png"))

        # 3) 音（repo直下/bgm.ogg）
        sound = SoundLoader.load(repo_path("bgm.ogg"))
        if sound:
            sound.loop = True
            sound.play()

        return banner


if __name__ == "__main__":
    Day6App().run()
