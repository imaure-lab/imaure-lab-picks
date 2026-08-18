"""generate_draft.pyで保存した下書きを確認し、承認したらInstagramに投稿する。

帰宅後など、都合の良いタイミングで手動実行する。
標準フローでは、投稿前にCanvaでブランド画像加工(enhanced_image_url)を済ませておく必要がある。
どうしても生画像のまま投稿したい場合のみ `--raw` オプションを付ける。
"""
import json
import sys
from datetime import datetime, timezone

from config import DATA_DIR, IG_ACCESS_TOKEN, IG_USER_ID
from history import append_post
from instagram_client import InstagramClientError, post_image
from landing_page import publish_landing_page
from qr_util import save_qr

DRAFT_PATH = DATA_DIR / "draft.json"
STALE_HOURS = 6


def main() -> None:
    allow_raw = "--raw" in sys.argv

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
    enhanced_image_url = draft.get("enhanced_image_url")

    print("=" * 50)
    print(f"注目商品: {top_item['name']}")
    print(f"順位: {top_item['rank']}位 / ステータス: {draft['top']['status']}")
    print(f"生画像URL: {top_item['image_url']}")
    print(f"強化済み画像URL: {enhanced_image_url or '(未加工)'}")
    print(f"生成日時: {generated_at.isoformat()}")
    print("-" * 50)
    print("投稿キャプション:")
    print(caption)
    print("=" * 50)
    affiliate_url = top_item.get("affiliate_url", top_item["url"])
    qr_path = save_qr(affiliate_url)
    print(f"★ プロフィールのリンクをこのURLに貼り替えてください:\n{affiliate_url}")
    print(f"★ QRコードも保存しました(スマホのカメラで読み取れます): {qr_path}")
    print("=" * 50)

    if not enhanced_image_url and not allow_raw:
        print(
            "\n[未加工] この下書きはまだCanvaでのブランド画像加工が済んでいません。"
            "\nClaudeに「この下書きの画像をテンプレートで強化して」と頼んでから、もう一度実行してください。"
            "\n(どうしても生画像のまま投稿する場合は `python approve_and_post.py --raw` を実行)"
        )
        sys.exit(1)

    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        print("\nIG_USER_ID / IG_ACCESS_TOKEN が未設定のため、投稿できません。")
        sys.exit(1)

    image_to_post = enhanced_image_url or top_item["image_url"]
    answer = input("\nこの内容でInstagramに投稿しますか? (yes/no): ").strip().lower()
    if answer not in ("y", "yes"):
        print("投稿をキャンセルしました。下書きは残しています。")
        return

    try:
        post_id = post_image(image_to_post, caption)
    except InstagramClientError as e:
        print(f"[エラー] 投稿に失敗しました: {e}")
        sys.exit(1)

    print(f"投稿完了しました。post_id={post_id}")

    append_post(top_item, image_to_post, post_id)
    publish_landing_page()

    DRAFT_PATH.unlink()  # 二重投稿防止のため下書きを削除


if __name__ == "__main__":
    main()
