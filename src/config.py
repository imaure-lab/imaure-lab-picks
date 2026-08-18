import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID", "")
RAKUTEN_ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY", "")
RAKUTEN_AFFILIATE_ID = os.getenv("RAKUTEN_AFFILIATE_ID", "")

# 防災関連グッズ, パソコン・周辺機器, 家電, スマートフォン・タブレット
_default_genres = "111519,100026,562637,564500"
RAKUTEN_GENRE_IDS = [g.strip() for g in os.getenv("RAKUTEN_GENRE_IDS", _default_genres).split(",") if g.strip()]

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)
