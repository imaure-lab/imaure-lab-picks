"""楽天ランキング取得 → トレンド分析 → キャプション生成 → (確認後)Instagram投稿。

手動実行前提のスクリプト。投稿(publish)の直前で必ず確認を挟む。

【注意】これは生画像のまま即時投稿する簡易版。Canvaでのブランド画像加工は挟まれない。
標準フローとして画像加工を必ず挟みたい場合は generate_draft.py → (Claudeに画像強化を依頼) →
approve_and_post.py を使うこと。
"""
import sys

from config import IG_ACCESS_TOKEN, IG_USER_ID
from dataclasses import asdict
from history import append_post
from instagram_client import InstagramClientError, post_image
from landing_page import publish_landing_page
from pipeline import PipelineError, build_draft
from qr_util import save_qr


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
    print("[注意] これは生画像のまま投稿する簡易版です(Canva加工なし)。")
    qr_path = save_qr(top.item.affiliate_url)
    print(f"★ プロフィールのリンクをこのURLに貼り替えてください:\n{top.item.affiliate_url}")
    print(f"★ QRコードも保存しました(スマホのカメラで読み取れます): {qr_path}")
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

    append_post(asdict(top.item), top.item.image_url, post_id)
    publish_landing_page()


if __name__ == "__main__":
    main()
