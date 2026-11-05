"""東京湾 釣れ予報：Open-Meteo から各エリアの7日分の海況・天気を取得し data/forecast.json に保存する。

GitHub Actions から1日数回実行する想定。標準ライブラリのみで動く（pip install 不要）。

- 海面水温・波高：Open-Meteo Marine API
- 風速・天気    ：Open-Meteo Forecast API
  ライセンス CC BY 4.0（画面にクレジット表記が必要）。無料枠は非商用向け。

取得に失敗したエリア・項目は null を入れ、画面側で仮の値に置き換える。
全エリアで取得に失敗した場合は既存の forecast.json を上書きしない（終了コード1）。
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "forecast.json"
JST = timezone(timedelta(hours=9))
DAYS = 7

# 各エリアの代表座標（海上の点。具体的な釣り場は指さない大まかな位置）
AREAS = [
    {"id": "wanoku", "lat": 35.55, "lon": 139.93},
    {"id": "yokohama", "lat": 35.45, "lon": 139.72},
    {"id": "uchibo", "lat": 35.35, "lon": 139.80},
    {"id": "wanko", "lat": 35.20, "lon": 139.75},
]

# 水温が取れなかったとき（海の格子が粗く湾奥が陸扱いになる等）に借りる隣のエリア
SST_FALLBACK = {"wanoku": "yokohama", "yokohama": "uchibo", "uchibo": "yokohama", "wanko": "uchibo"}

# 月別の海面水温 平年値（℃、概算）。気象庁「海面水温の平年値」を参照して今後置き換える。
NORMALS = {
    "wanoku":   [11.0, 10.2, 11.2, 14.0, 17.8, 21.3, 24.8, 26.8, 25.6, 22.0, 18.0, 14.0],
    "yokohama": [12.0, 11.2, 12.0, 14.5, 18.0, 21.3, 24.6, 26.5, 25.4, 22.3, 18.8, 15.0],
    "uchibo":   [13.0, 12.2, 12.8, 15.0, 18.3, 21.4, 24.5, 26.3, 25.4, 22.6, 19.3, 15.8],
    "wanko":    [15.0, 14.2, 14.6, 16.2, 18.8, 21.5, 24.3, 26.0, 25.3, 23.2, 20.4, 17.3],
}

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
UA = "tsuri-yoho/1.0 (+GitHub Actions)"


def get_json(url: str, params: dict, retries: int = 3) -> dict:
    full = url + "?" + urllib.parse.urlencode(params)
    last: Exception | None = None
    for i in range(retries):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.load(res)
        except Exception as e:  # ネットワーク一時エラーは少し待って再試行
            last = e
            time.sleep(2 ** (i + 1))
    raise RuntimeError(f"取得失敗: {url} ({last})")


def daily_mean_from_hourly(times: list[str], values: list, dates: list[str]) -> list:
    """毎時の値を日付ごとに平均する（null は除外）。"""
    buckets: dict[str, list[float]] = {d: [] for d in dates}
    for t, v in zip(times, values):
        d = t[:10]
        if d in buckets and v is not None:
            buckets[d].append(float(v))
    return [round(sum(b) / len(b), 1) if b else None for b in (buckets[d] for d in dates)]


def sky_from_code(code) -> str | None:
    """WMO天気コード → 日本語の大まかな天気。"""
    if code is None:
        return None
    c = int(code)
    if c <= 1:
        return "晴れ"
    if c <= 3 or c in (45, 48):
        return "くもり"
    if c in (71, 73, 75, 77, 85, 86):
        return "雪"
    if c >= 95:
        return "雷雨"
    return "雨"


def pick(daily: dict, key: str, dates: list[str]) -> list:
    idx = {d: i for i, d in enumerate(daily.get("time", []))}
    vals = daily.get(key, [])
    out = []
    for d in dates:
        i = idx.get(d)
        out.append(vals[i] if i is not None and i < len(vals) else None)
    return out


def fetch_area(area: dict, dates: list[str]) -> dict:
    base = {"latitude": area["lat"], "longitude": area["lon"], "timezone": "Asia/Tokyo", "forecast_days": DAYS}
    result = {"sst": [None] * DAYS, "wave": [None] * DAYS, "wind": [None] * DAYS, "sky": [None] * DAYS}
    errors = []
    try:
        m = get_json(MARINE_URL, {**base, "hourly": "sea_surface_temperature",
                                  "daily": "wave_height_max", "cell_selection": "sea"})
        h = m.get("hourly", {})
        result["sst"] = daily_mean_from_hourly(h.get("time", []), h.get("sea_surface_temperature", []), dates)
        result["wave"] = [None if v is None else round(float(v), 1)
                          for v in pick(m.get("daily", {}), "wave_height_max", dates)]
    except Exception as e:
        errors.append(str(e))
    try:
        f = get_json(FORECAST_URL, {**base, "daily": "weather_code,wind_speed_10m_max", "wind_speed_unit": "ms"})
        d = f.get("daily", {})
        result["wind"] = [None if v is None else round(float(v), 1) for v in pick(d, "wind_speed_10m_max", dates)]
        result["sky"] = [sky_from_code(c) for c in pick(d, "weather_code", dates)]
    except Exception as e:
        errors.append(str(e))
    if errors:
        result["errors"] = errors
    return result


def build(now: datetime | None = None) -> dict:
    now = now or datetime.now(JST)
    start = now.date()
    dates = [(start + timedelta(days=i)).isoformat() for i in range(DAYS)]
    areas = {}
    for a in AREAS:
        r = fetch_area(a, dates)
        r["norm"] = NORMALS[a["id"]][start.month - 1]
        areas[a["id"]] = r
    for aid, r in areas.items():
        if all(v is None for v in r["sst"]):
            src = areas[SST_FALLBACK[aid]]
            if any(v is not None for v in src["sst"]):
                r["sst"] = list(src["sst"])
                r["sst_from"] = SST_FALLBACK[aid]
    return {
        "generated_at": now.isoformat(timespec="minutes"),
        "start_date": dates[0],
        "dates": dates,
        "source": "Open-Meteo (CC BY 4.0)",
        "norm_note": "平年値は概算（気象庁の平年値で置き換え予定）",
        "areas": areas,
    }


def has_any_data(doc: dict) -> bool:
    return any(v is not None for a in doc["areas"].values() for k in ("sst", "wind") for v in a[k])


def main() -> int:
    doc = build()
    for aid, a in doc["areas"].items():
        print(aid, "sst", a["sst"], "wave", a["wave"], "wind", a["wind"], a.get("errors", ""))
    if not has_any_data(doc):
        print("全エリアで取得に失敗したため、既存の forecast.json を残します。", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("saved:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
