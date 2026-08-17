"""下書きを自動生成して保存するだけのスクリプト(投稿はしない・無人実行対応)。

タスクスケジューラ等から19時などに自動実行する想定。
生成した下書きは data/draft.json に保存され、approve_and_post.py で確認・投稿する。
"""
import json
import sys
import traceback
from dataclasses import asdict
from datetime import datetime, timezone

from config import DATA_DIR
from pipeline import PipelineError, build_draft

DRAFT_PATH = DATA_DIR / "draft.json"
LOG_PATH = DATA_DIR / "generate_draft.log"


def _log(message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def main() -> None:
    try:
        top, others, caption = build_draft()
    except PipelineError as e:
        _log(f"[エラー] {e}")
        sys.exit(1)
    except Exception:
        _log("[エラー] 予期しない例外が発生しました:\n" + traceback.format_exc())
        sys.exit(1)

    draft = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top": {"item": asdict(top.item), "status": top.status, "previous_rank": top.previous_rank},
        "others": [
            {"item": asdict(t.item), "status": t.status, "previous_rank": t.previous_rank}
            for t in others
        ],
        "caption": caption,
    }

    with open(DRAFT_PATH, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)

    _log(f"下書きを保存しました: {DRAFT_PATH}(注目商品: {top.item.name[:30]}...)")


if __name__ == "__main__":
    main()
