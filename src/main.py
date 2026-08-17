"""楽天ランキング取得 → トレンド分析 → キャプション生成 → (確認後)Instagram投稿。

手動実行前提のスクリプト。投稿(publish)の直前で必ず確認を挟む。
その場で確認できないタイミングで回したい場合は generate_draft.py + approve_and_post.py を使う。
"""
import sys

from config import IG_ACCESS_TOKEN, IG_USER_ID
from instagram_client import InstagramClientError, post_image
from pipeline import PipelineError, build_draft


def main() -> None:
    try:
        top, others, caption = build_draft()
    except PipelineError as e:
        print(f"[エラー] {e}")
        sys.exit(1)

    print("=" * 50)
    print(f"注目商品: {top.item.name}")
    print(f"順位: {top.item.rank}位 / ステータス: {top.status}")
    print(f"画像URL: {top.item.image_url}")
    print("-" * 50)
    print("投稿キャプション:")
    print(caption)
    print("=" * 50)

    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        print(
            "\nIG_USER_ID / IG_ACCESS_TOKEN が未設定のため、投稿はスキップします。"
            "\nInstagram連携の準備ができたら .env を設定して再実行してください。"
        )
        return

    if not top.item.image_url:
        print("\n[警告] 画像URLが取得できなかったため投稿できません。")
        return

    answer = input("\nこの内容でInstagramに投稿しますか? (yes/no): ").strip().lower()
    if answer not in ("y", "yes"):
        print("投稿をキャンセルしました。")
        return

    try:
        post_id = post_image(top.item.image_url, caption)
    except InstagramClientError as e:
        print(f"[エラー] 投稿に失敗しました: {e}")
        sys.exit(1)

    print(f"投稿完了しました。post_id={post_id}")


if __name__ == "__main__":
    main()
