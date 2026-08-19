"""投稿成功時に商品情報を記録する(ランディングページ生成用)。"""
import json
from datetime import datetime, timezone

import requests

from config import DATA_DIR, DOCS_DIR

HISTORY_PATH = DATA_DIR / "posted_history.json"
IMAGES_DIR = DOCS_DIR / "images"
MAX_ENTRIES = 30


def _mirror_image(image_url: str, post_id: str) -> str:
    """外部画像(Canvaの書き出しURLは数時間で失効する)をリポジトリ内に保存し、相対パスを返す。"""
    IMAGES_DIR.mkdir(exist_ok=True)
    dest = IMAGES_DIR / f"{post_id}.jpg"
    try:
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            f.write(resp.content)
        return f"images/{post_id}.jpg"
    except Exception as e:
        print(f"[history] 画像のミラー保存に失敗しました(元URLをそのまま使用): {e}")
        return image_url


def append_post(item: dict, image_url: str, post_id: str, ranking_at: str) -> None:
    """投稿成功後に呼び出す。

    item は RankedItem を dict化したもの。
    ranking_at は実際に楽天ランキングを取得した時刻(ISO形式)。
    投稿処理自体(承認待ちなど)は後からになるため、posted_atとは別に持つ。
    """
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    mirrored_image = _mirror_image(image_url, post_id)

    history.insert(
        0,
        {
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "ranking_at": ranking_at,
            "post_id": post_id,
            "name": item["name"],
            "price": item["price"],
            "rank": item["rank"],
            "image_url": mirrored_image,
            "affiliate_url": item.get("affiliate_url") or item.get("url", ""),
        },
    )
    history = history[:MAX_ENTRIES]

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
