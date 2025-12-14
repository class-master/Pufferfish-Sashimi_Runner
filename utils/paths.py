# -*- coding: utf-8 -*-
"""
Day6: パス矯正ユーティリティ
目的：
- 実行場所（カレントディレクトリ）に依存せず、常に正しい assets / bgm を見つける
- 「assets/...」の生文字列をコード中に散らさない

使い方（例）：
    from utils.paths import sanity_check, asset_path, repo_path
    sanity_check()
    Image(source=asset_path("neon_banner.png"))
    SoundLoader.load(repo_path("bgm.ogg"))
"""

from __future__ import annotations
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    """
    start から上に辿って「リポジトリ直下」を推定する。

    このプロジェクトでは、リポジトリ直下に
      - assets/ フォルダ
      - config.py
    があるので、それを目印にする。
    """
    p = start
    for _ in range(12):
        if (p / "assets").is_dir() and (p / "config.py").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    # 見つからない場合は「このファイルの1つ上（utilsの外）」を仮に返す
    return start.parent


# repo_root/utils/paths.py を想定
REPO_ROOT: Path = _find_repo_root(Path(__file__).resolve())
ASSETS_DIR: Path = REPO_ROOT / "assets"
BGM_PATH: Path = REPO_ROOT / "bgm.ogg"


def asset_file(*parts: str) -> Path:
    """assets配下の Path を返す（Pathで扱いたい時）"""
    return ASSETS_DIR.joinpath(*parts)


def asset_path(*parts: str) -> str:
    """assets配下のパスを str で返す（Kivyのsource等に渡しやすい）"""
    return str(asset_file(*parts))


def repo_file(*parts: str) -> Path:
    """repo直下の Path を返す"""
    return REPO_ROOT.joinpath(*parts)


def repo_path(*parts: str) -> str:
    """repo直下のパスを str で返す"""
    return str(repo_file(*parts))


def sanity_check(require_bgm: bool = True) -> None:
    """
    起動直後に呼ぶ用：
    - 直下の assets/ と config.py を見つけられているか
    - bgm.ogg があるか（require_bgm=True の場合）

    見つからない場合は、原因が分かるメッセージで落とす。
    """
    if not (REPO_ROOT / "config.py").exists():
        raise FileNotFoundError(
            "config.py が見つかりません。REPO_ROOT 推定に失敗しています。\n"
            f"REPO_ROOT={REPO_ROOT}\n"
            "ヒント：このリポジトリ直下に utils/ と assets/ と config.py がある構成を想定しています。"
        )
    if not ASSETS_DIR.is_dir():
        raise FileNotFoundError(
            "assets/ フォルダが見つかりません。\n"
            f"ASSETS_DIR={ASSETS_DIR}\n"
            f"REPO_ROOT={REPO_ROOT}"
        )
    if require_bgm and not BGM_PATH.exists():
        raise FileNotFoundError(
            "bgm.ogg が見つかりません。\n"
            f"BGM_PATH={BGM_PATH}\n"
            "ヒント：音素材の置き場所を Day6 で『repo直下』に統一します。"
        )
