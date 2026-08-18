"""投稿履歴からランディングページ(docs/index.html)を生成し、GitHub Pagesへpushする。

Instagramのフィード投稿のキャプション内リンクはタップできないため、
プロフィールの「ウェブサイト」欄をこのページのURLに固定しておき、
中身(おすすめ商品一覧)だけを投稿のたびに自動更新する。
"""
import json
import subprocess

from config import BASE_DIR, DATA_DIR, DOCS_DIR

HISTORY_PATH = DATA_DIR / "posted_history.json"
OUTPUT_PATH = DOCS_DIR / "index.html"


def _render_html(history: list[dict]) -> str:
    cards = []
    for entry in history:
        cards.append(f"""
        <a class="card" href="{entry['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener">
          <img src="{entry['image_url']}" alt="" loading="lazy">
          <div class="card-body">
            <p class="name">{entry['name'][:60]}</p>
            <p class="price">¥{entry['price']:,}</p>
            <span class="cta">購入はこちら →</span>
          </div>
        </a>""")

    cards_html = "\n".join(cards) if cards else '<p class="empty">近日更新予定です。</p>'

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>今売れ研 -imaure- おすすめ一覧</title>
<style>
  :root {{ --bg:#faf7f2; --card:#ffffff; --text:#2b2b2b; --accent:#e2734f; --sub:#8a8a8a; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:24px 16px 48px; background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic",sans-serif; }}
  header {{ text-align:center; margin-bottom:24px; }}
  header h1 {{ font-size:20px; margin:0 0 4px; }}
  header p {{ font-size:13px; color:var(--sub); margin:0; }}
  .grid {{ display:grid; gap:16px; max-width:480px; margin:0 auto; }}
  .card {{ display:flex; gap:12px; background:var(--card); border-radius:12px; padding:12px;
    text-decoration:none; color:inherit; box-shadow:0 1px 4px rgba(0,0,0,0.06); }}
  .card img {{ width:88px; height:88px; object-fit:cover; border-radius:8px; flex-shrink:0; background:#eee; }}
  .card-body {{ display:flex; flex-direction:column; justify-content:center; min-width:0; }}
  .name {{ font-size:13px; line-height:1.4; margin:0 0 6px; overflow:hidden; text-overflow:ellipsis;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }}
  .price {{ font-size:15px; font-weight:600; margin:0 0 6px; }}
  .cta {{ font-size:12px; color:var(--accent); font-weight:600; }}
  .empty {{ text-align:center; color:var(--sub); }}
  footer {{ text-align:center; margin-top:32px; font-size:11px; color:var(--sub); }}
</style>
</head>
<body>
<header>
  <h1>今売れ研 -imaure-</h1>
  <p>楽天市場のリアルタイムランキングから厳選 [PR]</p>
</header>
<div class="grid">
{cards_html}
</div>
<footer>本ページのリンクには広告(アフィリエイトリンク)が含まれます</footer>
</body>
</html>
"""


def publish_landing_page() -> None:
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    html = _render_html(history)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    _git_publish()


def _git_publish() -> None:
    try:
        remotes = subprocess.run(
            ["git", "remote"], cwd=BASE_DIR, capture_output=True, text=True, timeout=10
        )
        if "origin" not in remotes.stdout.split():
            print("[ランディングページ] git remote 'origin' が未設定のため、pushはスキップしました。")
            print(f"  (ローカルには {OUTPUT_PATH} を生成済みです)")
            return

        subprocess.run(["git", "add", "docs/index.html", "docs/images"], cwd=BASE_DIR, check=True, timeout=10)
        commit = subprocess.run(
            ["git", "commit", "-m", "Update landing page"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if commit.returncode != 0 and "nothing to commit" not in commit.stdout:
            print(f"[ランディングページ] コミットに失敗しました: {commit.stdout}{commit.stderr}")
            return

        push = subprocess.run(
            ["git", "push", "origin", "HEAD"], cwd=BASE_DIR, capture_output=True, text=True, timeout=30
        )
        if push.returncode != 0:
            print(f"[ランディングページ] pushに失敗しました: {push.stderr}")
        else:
            print("[ランディングページ] GitHub Pagesへpushしました。反映まで数分かかる場合があります。")
    except Exception as e:
        print(f"[ランディングページ] git操作でエラーが発生しました(スキップ): {e}")
