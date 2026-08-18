"""投稿成功時に商品情報を記録する(ランディングページ生成用)。"""
import json
from datetime import datetime, timezone

from config import DATA_DIR

HISTORY_PATH = DATA_DIR / "posted_history.json"
MAX_ENTRIES = 30


def append_post(item: dict, image_url: str, post_id: str) -> None:
    """投稿成功後に呼び出す。item は RankedItem を dict化したもの。"""
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    history.insert(
        0,
        {
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "post_id": post_id,
            "name": item["name"],
            "price": item["price"],
            "rank": item["rank"],
            "image_url": image_url,
            "affiliate_url": item.get("affiliate_url") or item.get("url", ""),
        },
    )
    history = history[:MAX_ENTRIES]

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
