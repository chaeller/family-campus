"""Writes the logo everywhere: www/favicon.svg, the inline logo in index.html and login.html, and Family
Campus icons in www/icons/ (PNG, rendered with headless Chromium via Playwright – a development tool only).
The logo: three heads (a family) looking over an open book – learning together.
usage: python3 tools/make_icons.py"""
import pathlib, re
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
WWW = ROOT / "www"
ACCENT = "#6b4eff"

# the mark on a 64×64 grid, without background
GLYPH = (
    '<g fill="#fff"><circle cx="19" cy="22" r="6.5"/><circle cx="45" cy="22" r="6.5"/><circle cx="32" cy="27" r="5.5"/>'
    '<path d="M8 40a11 10 0 0 1 22 0zM34 40a11 10 0 0 1 22 0zM23 41a9 8 0 0 1 18 0z" opacity=".8"/></g>'
    f'<path d="M8 41q12-5 24 1q12-6 24-1v12q-12-5-24 1q-12-6-24-1z" fill="#fff" stroke="{ACCENT}" stroke-width="3" stroke-linejoin="round"/>'
    f'<path d="M32 42v12" stroke="{ACCENT}" stroke-width="2.5"/>'
)
ROUNDED = f'<rect width="64" height="64" rx="14" fill="{ACCENT}"/>' + GLYPH


def svg(inner, attrs=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"{attrs}>{inner}</svg>'


def full_bleed(scale):
    """square background without rounded corners, the mark scaled around the centre (safe zone for maskable icons)"""
    off = 32 * (1 - scale)
    return f'<rect width="64" height="64" fill="{ACCENT}"/><g transform="translate({off} {off}) scale({scale})">{GLYPH}</g>'


def main():
    (WWW / "favicon.svg").write_text(svg(ROUNDED) + "\n", encoding="utf-8")
    # inline logo in the page headers (same markup, only the size differs)
    for page, size in (("index.html", 52), ("login.html", 48)):
        p = WWW / page
        s = p.read_text(encoding="utf-8")
        new = f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">{ROUNDED}</svg>'
        s, n = re.subn(r'<svg width="%d" height="%d" viewBox="0 0 64 64" aria-hidden="true">.*?</svg>' % (size, size), new, s, count=1, flags=re.S)
        assert n == 1, page
        p.write_text(s, encoding="utf-8")
    icons = {  # file: (pixels, svg content, transparent corners?)
        "icon-192.png": (192, ROUNDED, True),
        "icon-512.png": (512, ROUNDED, True),
        "icon-maskable-512.png": (512, full_bleed(0.78), False),   # content inside the 80 % safe circle
        "apple-touch-icon.png": (180, full_bleed(0.86), False),    # iOS rounds the corners itself
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, (px, inner, transparent) in icons.items():
            page = browser.new_page(viewport={"width": px, "height": px})
            page.set_content(f'<html><body style="margin:0;background:transparent">{svg(inner, f" width=\'{px}\' height=\'{px}\'")}</body></html>')
            page.locator("svg").screenshot(path=str(WWW / "icons" / name), omit_background=transparent)
            page.close()
        browser.close()
    print("logo and icons written")


if __name__ == "__main__":
    main()
