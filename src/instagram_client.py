"""Instagram API (Instagramログイン方式) 投稿クライアント(画像1枚投稿・2段階方式)。

事前準備が必要:
- Instagram Business/Creatorアカウント
- Instagramログインで発行した instagram_business_content_publish 権限を持つアクセストークン
  (Facebookページ連携は不要)
"""
import time

import requests

from config import IG_ACCESS_TOKEN, IG_USER_ID

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.instagram.com/{GRAPH_API_VERSION}"


class InstagramClientError(RuntimeError):
    pass


def _check_credentials() -> None:
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        raise InstagramClientError(
            "IG_USER_ID / IG_ACCESS_TOKEN が設定されていません(.envを確認してください)"
        )


def create_media_container(image_url: str, caption: str) -> str:
    """画像URLとキャプションからメディアコンテナを作成し、creation_idを返す。"""
    _check_credentials()
    url = f"{GRAPH_BASE}/{IG_USER_ID}/media"
    resp = requests.post(
        url,
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=30,
    )
    body = resp.json()
    if resp.status_code != 200 or "id" not in body:
        raise InstagramClientError(f"メディアコンテナ作成に失敗しました: {body}")
    return body["id"]


def _wait_until_ready(creation_id: str, timeout_sec: int = 60) -> None:
    url = f"{GRAPH_BASE}/{creation_id}"
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        resp = requests.get(
            url, params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN}, timeout=15
        )
        body = resp.json()
        status = body.get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise InstagramClientError(f"メディア処理でエラーが発生しました: {body}")
        time.sleep(2)
    raise InstagramClientError("メディア処理がタイムアウトしました")


def publish_media(creation_id: str) -> str:
    """作成済みメディアコンテナを公開し、投稿IDを返す。"""
    _check_credentials()
    _wait_until_ready(creation_id)

    url = f"{GRAPH_BASE}/{IG_USER_ID}/media_publish"
    resp = requests.post(
        url,
        data={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
        timeout=30,
    )
    body = resp.json()
    if resp.status_code != 200 or "id" not in body:
        raise InstagramClientError(f"投稿の公開に失敗しました: {body}")
    return body["id"]


def post_image(image_url: str, caption: str) -> str:
    """画像投稿を一括で行うヘルパー。投稿済み投稿IDを返す。"""
    creation_id = create_media_container(image_url, caption)
    return publish_media(creation_id)
