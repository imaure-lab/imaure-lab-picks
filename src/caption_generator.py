"""トレンド商品からInstagram投稿用キャプションを生成する。

ANTHROPIC_API_KEY が設定されていればClaudeで生成し、無ければテンプレートで代用する。
"""
from analyzer import TrendItem
from config import ANTHROPIC_API_KEY

STATUS_LABEL = {
    "new": "初登場",
    "up": "急上昇",
    "steady": "人気継続中",
}


def _template_caption(top: TrendItem, others: list[TrendItem]) -> str:
    item = top.item
    label = STATUS_LABEL[top.status]
    lines = [
        f"【{label}】{item.name}",
        f"楽天リアルタイムランキング {item.rank}位!",
        f"¥{item.price:,}(税込) / レビュー{item.review_count}件 ★{item.review_average}",
        "",
    ]
    if others:
        lines.append("他にも注目の商品:")
        for t in others[:3]:
            lines.append(f"・{t.item.name}({STATUS_LABEL[t.status]} {t.item.rank}位)")
        lines.append("")
    lines.append("#楽天市場 #楽天ランキング #トレンド #お買い物 #新商品")
    return "\n".join(lines)


def generate_caption(top: TrendItem, others: list[TrendItem] | None = None) -> str:
    others = others or []
    if not ANTHROPIC_API_KEY:
        return _template_caption(top, others)

    from anthropic import Anthropic

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    item = top.item
    others_text = "\n".join(f"- {t.item.name}({STATUS_LABEL[t.status]}, {t.item.rank}位)" for t in others[:3])

    prompt = f"""あなたは楽天市場の商品を紹介するInstagram運用担当です。
以下の商品情報をもとに、Instagram投稿用のキャプションを日本語で作成してください。

【メイン商品】
商品名: {item.name}
ステータス: {STATUS_LABEL[top.status]}
現在の順位: {item.rank}位
価格: {item.price}円
レビュー件数: {item.review_count}件 / 平均評価: {item.review_average}

【あわせて紹介する商品(任意で軽く触れる程度)】
{others_text or "なし"}

要件:
- 3〜5文程度、親しみやすく購買意欲を引く文体
- 価格やランキング順位などの事実は誇張せず正確に書く
- 効果効能や医薬品的な断定表現は使わない
- 最後に関連ハッシュタグを5〜8個つける(#楽天市場 #楽天ランキング を含める)
- キャプション本文のみを出力し、前置きや説明文は付けない
"""

    resp = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()
