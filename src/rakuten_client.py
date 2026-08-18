"""楽天ウェブサービス IchibaItem/Ranking API クライアント。

API仕様: https://webservice.rakuten.co.jp/api/ichibaranking/
"""
from dataclasses import dataclass

import requests

from config import RAKUTEN_ACCESS_KEY, RAKUTEN_AFFILIATE_ID, RAKUTEN_APP_ID

RANKING_ENDPOINT = "https://openapi.rakuten.co.jp/ichibaranking/api/IchibaItem/Ranking/20220601"


@dataclass
class RankedItem:
    rank: int
    item_code: str
    name: str
    url: str
    affiliate_url: str
    price: int
    shop_name: str
    review_count: int
    review_average: float
    image_url: str


class RakutenClientError(RuntimeError):
    pass


def fetch_realtime_ranking(genre_id: str = "0", page: int = 1) -> list[RankedItem]:
    """リアルタイムランキングを取得する。genre_id='0'は総合ランキング。"""
    if not RAKUTEN_APP_ID or not RAKUTEN_ACCESS_KEY:
        raise RakutenClientError(
            "RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY が設定されていません(.envを確認してください)"
        )

    params = {
        "format": "json",
        "applicationId": RAKUTEN_APP_ID,
        "accessKey": RAKUTEN_ACCESS_KEY,
        "genreId": genre_id,
        "period": "realtime",
        "page": page,
    }
    if RAKUTEN_AFFILIATE_ID:
        params["affiliateId"] = RAKUTEN_AFFILIATE_ID
    resp = requests.get(RANKING_ENDPOINT, params=params, timeout=15)
    if resp.status_code != 200:
        raise RakutenClientError(
            f"楽天API呼び出しに失敗しました: status={resp.status_code} body={resp.text[:300]}"
        )

    body = resp.json()
    items: list[RankedItem] = []
    for entry in body.get("Items", []):
        item = entry.get("Item", entry)
        image_urls = item.get("mediumImageUrls") or []
        image_url = ""
        if image_urls:
            raw = image_urls[0]
            image_url = raw.get("imageUrl", raw) if isinstance(raw, dict) else raw
            # 楽天の画像URLはサイズ指定クエリが付くことがあるため除去して原寸に近い形にする
            image_url = image_url.split("?")[0] if isinstance(image_url, str) else ""

        items.append(
            RankedItem(
                rank=item.get("rank", 0),
                item_code=item.get("itemCode", ""),
                name=item.get("itemName", ""),
                url=item.get("itemUrl", ""),
                affiliate_url=item.get("affiliateUrl") or item.get("itemUrl", ""),
                price=int(item.get("itemPrice", 0) or 0),
                shop_name=item.get("shopName", ""),
                review_count=int(item.get("reviewCount", 0) or 0),
                review_average=float(item.get("reviewAverage", 0.0) or 0.0),
                image_url=image_url,
            )
        )
    return items
