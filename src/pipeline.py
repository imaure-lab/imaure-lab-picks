"""楽天ランキング取得 → トレンド分析 → キャプション生成、までの共通ロジック。

main.py(即時実行)とgenerate_draft.py(スケジュール実行用の下書き生成)の両方から使う。
"""
import time

from analyzer import TrendItem, detect_trends, merge_trends
from caption_generator import generate_caption
from config import RAKUTEN_GENRE_IDS
from rakuten_client import RakutenClientError, fetch_realtime_ranking


class PipelineError(RuntimeError):
    pass


class NoTrendingItemError(PipelineError):
    """新規ランクイン・急上昇の商品が無かった(=先読み価値のある候補が無かった)場合。"""


# 「定番(steady)」は楽天の公式ランキング・おすすめ表示と重複しやすく、
# 「他の人より先に知れた」という価値を示せないため投稿候補から除外する。
QUALIFYING_STATUSES = {"new", "up"}


def build_draft() -> tuple[TrendItem, list[TrendItem], str]:
    """全ジャンルを取得・分析し、(トップ商品, その他候補, キャプション)を返す。

    新規ランクイン・急上昇の商品が無い場合は NoTrendingItemError を送出する
    (定番商品は楽天の公式ランキングと重複するだけで「先読み」の価値が無いため)。
    """
    trend_lists = []
    for i, genre_id in enumerate(RAKUTEN_GENRE_IDS):
        if i > 0:
            time.sleep(1.2)  # 楽天APIのレート制限(約1req/秒)対策
        try:
            items = fetch_realtime_ranking(genre_id=genre_id)
        except RakutenClientError as e:
            print(f"[エラー] 楽天ランキング取得に失敗しました(genreId={genre_id}): {e}")
            continue
        if items:
            trend_lists.append(detect_trends(items, genre_id, top_n=10))

    if not trend_lists:
        raise PipelineError("ランキングデータが取得できませんでした。")

    trends = merge_trends(trend_lists, top_n=10)
    qualifying = [t for t in trends if t.status in QUALIFYING_STATUSES]

    if not qualifying:
        raise NoTrendingItemError(
            "新規ランクイン・急上昇の商品が見つかりませんでした。"
            "定番商品は楽天の公式ランキングと同じになるため、本日の投稿はスキップします。"
        )

    top, others = qualifying[0], qualifying[1:]
    caption = generate_caption(top, others)
    return top, others, caption
