"""Static checks for the Cereysus brand assets, PWA icons and favicon wiring (Batch 0D).

They read the shipped files, so they run without a browser.
"""
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "assets/branding/cereysus"

# Source file in assets/branding/cereysus -> copy the app serves.
SHIPPED = {
    "cereysus-hardhat.svg": "static/branding/cereysus-hardhat.svg",
    "icon-192.png": "static/icons/icon-192.png",
    "icon-512.png": "static/icons/icon-512.png",
    "icon-maskable-512.png": "static/icons/icon-maskable-512.png",
    "apple-touch-icon-180.png": "static/icons/apple-touch-icon-180.png",
    "icon.ico": "static/icon.ico",
}
BOAT_PATH = "M16 4L16 22L6 22Z"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_shipped_copies_are_byte_identical_to_the_sources() -> None:
    for source, shipped in SHIPPED.items():
        assert (SOURCES / source).read_bytes() == (ROOT / shipped).read_bytes(), shipped


def test_manifest_keeps_any_and_maskable_icons_apart() -> None:
    icons = json.loads(_read("static/manifest.json"))["icons"]
    by_src = {icon["src"]: icon for icon in icons}
    assert by_src["icons/icon-192.png"]["purpose"] == "any"
    assert by_src["icons/icon-512.png"]["purpose"] == "any"
    assert by_src["icons/icon-maskable-512.png"]["purpose"] == "maskable"
    for icon in icons:
        assert "maskable" not in icon["purpose"].split() or icon["purpose"] == "maskable"


def test_maskable_icon_is_opaque_with_artwork_inside_the_safe_zone() -> None:
    image = Image.open(ROOT / "static/icons/icon-maskable-512.png").convert("RGBA")
    width, height = image.size
    pixels = image.load()
    background = pixels[0, 0]
    assert background[3] == 255
    radius = 0.4 * width  # the maskable safe zone is a circle of 80 % of the icon size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            assert a == 255
            if abs(r - background[0]) + abs(g - background[1]) + abs(b - background[2]) > 12:
                assert math.hypot(x - (width - 1) / 2, y - (height - 1) / 2) <= radius, (x, y)


def test_apple_touch_icon_is_opaque() -> None:
    image = Image.open(ROOT / "static/icons/apple-touch-icon-180.png").convert("RGBA")
    assert image.size == (180, 180)
    assert image.getchannel("A").getextrema() == (255, 255)


def test_wordmark_svg_is_outlined_and_static() -> None:
    source = (SOURCES / "cereysus-wordmark.svg").read_text(encoding="utf-8")
    root = ET.fromstring(source.encode("utf-8"))
    assert root.get("viewBox") == "0 0 168 40"
    assert "<text" not in source, "the lettering must be outlines (DEC-10)"
    assert "var(" not in source, "CSS variables do not apply inside an <img>"
    assert 'fill="#C9A87C"' in source


def test_pages_use_the_hard_hat_instead_of_the_boat() -> None:
    index, login, theme = _read("static/index.html"), _read("static/login.html"), _read("static/js/theme.js")
    for text in (index, login, theme):
        assert BOAT_PATH not in text
    assert 'src="/static/branding/cereysus-hardhat.svg"' in index
    assert 'class="welcome-boat"' in index
    assert 'src="static/branding/cereysus-hardhat.svg"' in login
    assert '<link rel="icon" sizes="192x192" href="/static/icons/icon-192.png">' in index
    assert 'rel="apple-touch-icon" sizes="180x180" href="/static/icons/apple-touch-icon-180.png"' in index
    assert 'rel="apple-touch-icon" sizes="180x180" href="static/icons/apple-touch-icon-180.png"' in login
    # The root route keeps the static icon; only per-route line icons follow the theme accent.
    assert "if (!routeShape) return;" in theme


def test_service_worker_precaches_the_new_assets() -> None:
    worker = _read("static/sw.js")
    assert "'/static/icons/apple-touch-icon-180.png'" in worker
    assert "'/static/branding/cereysus-hardhat.svg'" in worker


def test_launcher_draws_the_hard_hat() -> None:
    launcher = _read("launcher.py")
    assert "\u26f5" not in launcher, "the sailboat glyph is gone"
    assert 'text="Cereysus"' in launcher
    assert "icon-192.png" in launcher
