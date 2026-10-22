"""Static checks for the Cereysus themes (Batch 0C).

They read the shipped source files, so they run without a browser. Screenshots and
computed-style checks need a browser and are covered by the owner's visual check.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME_JS = (ROOT / "static/js/theme.js").read_text(encoding="utf-8")
TOKENS_CSS = (ROOT / "static/css/00-tokens.css").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "static/index.html").read_text(encoding="utf-8")
LOGIN_HTML = (ROOT / "static/login.html").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "static/manifest.json").read_text(encoding="utf-8"))

# The owner's palette, exactly as written in the Development Prompt (7.1).
OWNER_LIGHT = {
    "--bg": "#F3F3F3", "--bg2": "#EAEAEA", "--card": "#FFFFFF",
    "--primary": "#3D5A80", "--primary-bg": "#3D5A80", "--accent": "#C6A680",
    "--accent2": "#DDBB99", "--text": "#1A2B44", "--text2": "#2C2C2C",
    "--border": "#E5D1B8", "--border2": "#D4C4A8",
}
OWNER_DARK = {
    "--bg": "#1B1B3A", "--bg2": "#141428", "--card": "#252441",
    "--primary": "#2EC4CF", "--primary-bg": "#0F7A85", "--accent": "#C9A87C",
    "--accent2": "#367BB9", "--text": "#E6E9F2", "--text2": "#B8BFCF",
    "--border": "#2E2D55", "--border2": "#3A3968",
}
# Owner token -> engine keys (Development Prompt 7.3).
MAPPING = {
    "--bg": ["bg"], "--text": ["fg"], "--card": ["panel", "aiBubbleBg"],
    "--border": ["border"], "--primary": ["red"],
    "--primary-bg": ["sendBtnBg", "toggleActive"], "--accent": ["brandColor"],
    "--bg2": ["userBubbleBg", "sidebarBg"], "--text2": ["text2"],
    "--border2": ["bubbleBorder"],
}


def _themes_block() -> str:
    start = THEME_JS.index("export const THEMES = {")
    return THEME_JS[start:THEME_JS.index("\n};", start)]


def _preset_keys() -> list[str]:
    return [m.group(2) for m in re.finditer(r"^  ('?)([\w-]+)\1:\s*\{", _themes_block(), re.M)]


def _preset_values(name: str) -> dict[str, str]:
    block = _themes_block()
    heads = list(re.finditer(r"^  ('?)([\w-]+)\1:\s*\{", block, re.M))
    for i, head in enumerate(heads):
        if head.group(2) == name:
            end = heads[i + 1].start() if i + 1 < len(heads) else len(block)
            return {k: v.lower() for k, v in re.findall(r"\b(\w+):\s*'(#[0-9A-Fa-f]{6})'", block[head.start():end])}
    raise AssertionError(f"preset {name} not found")


def _channel(c: int) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_both_presets_carry_the_owners_exact_palette() -> None:
    for name, owner in (("cereysus-dark", OWNER_DARK), ("cereysus-light", OWNER_LIGHT)):
        preset = _preset_values(name)
        for token, keys in MAPPING.items():
            for key in keys:
                assert preset[key] == owner[token].lower(), f"{name}.{key} should be {owner[token]} ({token})"
        assert preset["brandMixTo"] == owner["--accent2"].lower()


def test_documented_deviations_from_the_proposed_mapping() -> None:
    dark = _preset_values("cereysus-dark")
    light = _preset_values("cereysus-light")
    # DEC-4: input borders are derived so they reach 3:1 against the surfaces they sit on.
    assert light["inputBorder"] == "#8f8b83"
    assert dark["inputBorder"] == "#717092"
    # Dark keeps the owner's accent2 as hover; light cannot (white on #DDBB99 is 1.8:1).
    assert dark["sendBtnHover"] == OWNER_DARK["--accent2"].lower()
    assert light["sendBtnHover"] == "#314866"


def test_cereysus_presets_come_first_and_upstream_presets_are_kept() -> None:
    keys = _preset_keys()
    assert keys[:2] == ["cereysus-dark", "cereysus-light"]
    for upstream in ("dark", "light", "midnight", "cyberpunk", "retrowave", "forest", "ocean", "ume",
                     "terminal", "organs", "gpt", "claude", "cute", "eclipse", "porcelain", "arcade",
                     "blueprint", "monolith", "yoyo"):
        assert upstream in keys


def test_default_theme_is_cereysus_dark_and_server_whitelist_matches() -> None:
    from src.theme_palette import THEME_PRESETS

    assert "const DEFAULT_THEME = 'cereysus-dark';" in THEME_JS
    assert THEME_PRESETS[:2] == ("cereysus-dark", "cereysus-light")
    assert set(THEME_PRESETS) == set(_preset_keys())
    assert "'cereysus-dark': 'Cereysus Dark'" in THEME_JS
    assert "'cereysus-light': 'Cereysus Light'" in THEME_JS


def test_text2_is_published_by_the_engine_and_mapped_to_muted_text() -> None:
    assert "s.setProperty('--cereysus-text2', colors.text2)" in THEME_JS
    assert "s.removeProperty('--cereysus-text2')" in THEME_JS
    assert "--color-muted: var(--cereysus-text2, #888);" in TOKENS_CSS


def test_duplicated_defaults_match_the_default_theme() -> None:
    dark = _preset_values("cereysus-dark")
    root = TOKENS_CSS.split(":root {", 1)[1].split("}", 1)[0].lower()
    for css_var, key in (("--bg", "bg"), ("--fg", "fg"), ("--panel", "panel"), ("--border", "border"), ("--red", "red")):
        assert f"{css_var}: {dark[key]};" in root
    login_root = LOGIN_HTML.split(":root {", 1)[1].split("}", 1)[0].lower()
    for css_var, key in (("--bg", "bg"), ("--fg", "fg"), ("--panel", "panel"), ("--border", "border"), ("--red", "red")):
        assert f"{css_var}: {dark[key]};" in login_root
    assert f"--brand-color: {dark['brandColor']};" in login_root
    assert f'<meta name="theme-color" content="{OWNER_DARK["--bg"]}">' in INDEX_HTML
    assert f"background:var(--bg,{OWNER_DARK['--bg']})" in INDEX_HTML
    assert MANIFEST["theme_color"].lower() == dark["bg"]
    assert MANIFEST["background_color"].lower() == dark["bg"]


def test_text_and_control_contrast_meets_wcag_aa() -> None:
    for name in ("cereysus-dark", "cereysus-light"):
        p = _preset_values(name)
        for surface in (p["bg"], p["panel"]):
            assert contrast(p["fg"], surface) >= 4.5, (name, "text")
            assert contrast(p["text2"], surface) >= 4.5, (name, "text2")
            assert contrast(p["red"], surface) >= 4.5, (name, "primary used as link or focus text")
            assert contrast(p["inputBorder"], surface) >= 3.0, (name, "input border")
        assert contrast("#ffffff", p["sendBtnBg"]) >= 4.5, (name, "send button label")
        assert contrast("#ffffff", p["sendBtnHover"]) >= 3.0, (name, "send button hover icon")
        assert contrast(p["fg"], p["userBubbleBg"]) >= 4.5, (name, "user bubble")


def _mix_with_black(hex_color: str, percent: int) -> str:
    h = hex_color.lstrip("#")
    return "#" + "".join(f"{round(int(h[i:i + 2], 16) * percent / 100):02x}" for i in (0, 2, 4))


def test_login_button_label_stays_readable_on_the_default_theme() -> None:
    dark = _preset_values("cereysus-dark")
    assert "--login-btn-mix: 66%;" in LOGIN_HTML and "--login-btn-hover-mix: 56%;" in LOGIN_HTML
    assert "var(--red) var(--login-btn-mix, 78%)" in LOGIN_HTML
    assert contrast("#ffffff", _mix_with_black(dark["red"], 66)) >= 4.5
    assert contrast("#ffffff", _mix_with_black(dark["red"], 56)) >= 4.5
    # Upstream themes keep their original 78 % / 66 % mixes.
    assert "cyDark ? '66%' : '78%'" in LOGIN_HTML
