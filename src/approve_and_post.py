"""generate_draft.pyで保存した下書きを確認し、承認したらInstagramに投稿する。

帰宅後など、都合の良いタイミングで手動実行する。
"""
import json
import sys
from datetime import datetime, timezone

from config import DATA_DIR, IG_ACCESS_TOKEN, IG_USER_ID
from instagram_client import InstagramClientError, post_image

DRAFT_PATH = DATA_DIR / "draft.json"
STALE_HOURS = 6


def main() -> None:
    if not DRAFT_PATH.exists():
        print(f"下書きが見つかりません: {DRAFT_PATH}")
        print("先に generate_draft.py を実行してください。")
        sys.exit(1)

    with open(DRAFT_PATH, encoding="utf-8") as f:
        draft = json.load(f)

    generated_at = datetime.fromisoformat(draft["generated_at"])
    age_hours = (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
    if age_hours > STALE_HOURS:
        print(f"[警告] この下書きは{age_hours:.1f}時間前に生成されたものです。ランキングが変わっている可能性があります。")

    top_item = draft["top"]["item"]
    caption = draft["caption"]

    print("=" * 50)
    print(f"注目商品: {top_item['name']}")
    print(f"順位: {top_item['rank']}位 / ステータス: {draft['top']['status']}")
    print(f"画像URL: {top_item['image_url']}")
    print(f"生成日時: {generated_at.isoformat()}")
    print("-" * 50)
    print("投稿キャプション:")
    print(caption)
    print("=" * 50)

    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        print("\nIG_USER_ID / IG_ACCESS_TOKEN が未設定のため、投稿できません。")
        sys.exit(1)

    answer = input("\nこの内容でInstagramに投稿しますか? (yes/no): ").strip().lower()
    if answer not in ("y", "yes"):
        print("投稿をキャンセルしました。下書きは残しています。")
        return

    try:
        post_id = post_image(top_item["image_url"], caption)
    except InstagramClientError as e:
        print(f"[エラー] 投稿に失敗しました: {e}")
        sys.exit(1)

    print(f"投稿完了しました。post_id={post_id}")
    DRAFT_PATH.unlink()  # 二重投稿防止のため下書きを削除


if __name__ == "__main__":
    main()
