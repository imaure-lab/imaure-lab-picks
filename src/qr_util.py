"""アフィリエイトURLをQRコード画像にする(PC→スマホへのURL受け渡し用)。"""
import qrcode

from config import DATA_DIR

QR_PATH = DATA_DIR / "affiliate_link_qr.png"


def save_qr(url: str) -> "str":
    img = qrcode.make(url)
    img.save(QR_PATH)
    return str(QR_PATH)
