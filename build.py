#!/usr/bin/env python3
"""
build.py — Regenerates the gallery section in index.html from radios/*.json files.

To add a new radio:
  1. Create a new .json file in the radios/ folder (copy any existing one as a template)
  2. Run: python3 build.py

Radio JSON fields:
  year           (int)    — e.g. 1940
  model          (str)    — e.g. "Philco Model 40-180"
  image          (str)    — filename relative to project root, e.g. "radio-1-philco.jpg"
  price          (int)    — e.g. 850
  sold           (bool)   — true or false
  description_en (str)    — English description
  description_es (str)    — Spanish description
"""

import json
import re
from pathlib import Path

RADIOS_DIR = Path(__file__).parent / "radios"
INDEX_HTML = Path(__file__).parent / "index.html"

GALLERY_START = "<!-- GALLERY:START -->"
GALLERY_END   = "<!-- GALLERY:END -->"


def load_radios():
    files = sorted(RADIOS_DIR.glob("*.json"))
    radios = []
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
            data["_file"] = f.name
            radios.append(data)
    return radios


def format_price(price):
    return f"{price:,}€".replace(",", ".")


def render_card(radio, index):
    year          = radio["year"]
    model         = radio["model"]
    image         = radio["image"]
    status        = radio.get("status", "sale")  # "sale", "sold", or "collection"
    desc_en       = radio["description_en"]
    desc_es       = radio["description_es"]
    i18n_key_desc = f"radio{index}.desc"

    overlay = ""
    position_relative = ''

    if status == "sold":
        position_relative = ' position: relative;'
        overlay = """
                        <div style="position: absolute; top: 0; right: 0; width: 250px; height: 250px; overflow: hidden; z-index: 10; pointer-events: none;">
                            <div style="position: absolute; top: 55px; right: -70px; width: 350px; transform: rotate(45deg); background: linear-gradient(135deg, #8B0000 0%, #B22222 50%, #8B0000 100%); color: #f5ebe0; text-align: center; padding: 0.6rem 0; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.25em; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5); border-top: 1px solid rgba(212, 175, 55, 0.85); border-bottom: 1px solid rgba(212, 175, 55, 0.85);" data-i18n="gallery.sold">Sold</div>
                        </div>"""

    if status == "sold":
        price = radio.get("price", 0)
        action_row = f"""
                            <span style="font-family: 'Playfair Display', serif; font-size: 1.5rem; color: var(--tube-glow); font-weight: 700; text-decoration: line-through; opacity: 0.5;">{format_price(price)}</span>
                            <span style="font-family: 'IBM Plex Mono', monospace; padding: 0.5rem 1rem; font-size: 0.75rem; opacity: 0.5;" data-i18n="gallery.sold">Sold</span>"""
    elif status == "collection":
        action_row = """
                            <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; color: var(--copper); text-transform: uppercase; letter-spacing: 0.15em; opacity: 0.8;" data-i18n="gallery.collection">Personal Collection</span>
                            <span></span>"""
    else:  # sale
        price = radio.get("price", 0)
        action_row = f"""
                            <span style="font-family: 'Playfair Display', serif; font-size: 1.5rem; color: var(--tube-glow); font-weight: 700;">{format_price(price)}</span>
                            <a href="mailto:info@arstechnica.shop?subject=Inquiry: {model}" style="font-family: 'IBM Plex Mono', monospace; background: transparent; border: 2px solid var(--copper); color: var(--radio-warm); padding: 0.5rem 1rem; text-transform: uppercase; letter-spacing: 0.15em; font-size: 0.75rem; text-decoration: none; transition: all 0.3s;" data-i18n="gallery.inquire">Inquire</a>"""

    return f"""
                    <div class="service-card" data-status="{status}" style="padding: 0; overflow: hidden; display: flex; flex-direction: column;{position_relative}">{overlay}
                        <div style="width: 100%; aspect-ratio: 4/3; overflow: hidden; flex-shrink: 0;">
                            <img src="{image}" alt="{year} {model}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>
                        <div style="padding: 1.5rem; display: flex; flex-direction: column; flex: 1;">
                            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; color: var(--copper); text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 0.5rem;">{year}</div>
                            <h4 style="margin-bottom: 0.8rem;">{model}</h4>
                            <p style="margin-bottom: 0; font-size: 0.95rem; flex: 1;" data-i18n="{i18n_key_desc}">{desc_en}</p>
                            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 1rem; margin-top: 1rem; border-top: 1px solid rgba(184, 115, 51, 0.3);">{action_row}
                            </div>
                        </div>
                    </div>"""


def render_gallery(radios):
    cards = "".join(render_card(r, i + 1) for i, r in enumerate(radios))
    return f"""{GALLERY_START}
                {cards}
                {GALLERY_END}"""


def build_translations(radios):
    en_entries = {}
    es_entries = {}
    for i, radio in enumerate(radios):
        key = f"radio{i + 1}.desc"
        en_entries[key] = radio["description_en"]
        es_entries[key] = radio["description_es"]
    return en_entries, es_entries


def update_translations(html, en_entries, es_entries):
    """Replace radio*.desc keys inside each language block independently."""

    def find_lang_block(html, lang_key):
        """Return (start, end) character offsets of the content inside lang: { ... }."""
        marker = f"{lang_key}: {{"
        start = html.find(marker)
        if start == -1:
            return None, None
        brace_start = html.index("{", start + len(lang_key))
        depth = 0
        for i in range(brace_start, len(html)):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
                if depth == 0:
                    return brace_start, i + 1
        return None, None

    def replace_keys_in_slice(block, entries):
        for key, value in entries.items():
            escaped = value.replace("'", "\\'")
            pattern = rf"('{re.escape(key)}'\s*:\s*')[^']*(')"
            block = re.sub(pattern, rf"\g<1>{escaped}\g<2>", block)
        return block

    for lang_key, entries in [("en", en_entries), ("es", es_entries)]:
        start, end = find_lang_block(html, lang_key)
        if start is None:
            continue
        block = html[start:end]
        block = replace_keys_in_slice(block, entries)
        html = html[:start] + block + html[end:]

    return html


def main():
    radios = load_radios()
    if not radios:
        print("No radio JSON files found in radios/")
        return

    html = INDEX_HTML.read_text()

    # Replace gallery section
    start_idx = html.find(GALLERY_START)
    end_idx   = html.find(GALLERY_END)

    if start_idx == -1 or end_idx == -1:
        print(f"Error: Could not find {GALLERY_START!r} / {GALLERY_END!r} markers in index.html")
        print("Please add these markers around the gallery cards in index.html first.")
        return

    new_gallery = render_gallery(radios)
    html = html[:start_idx] + new_gallery + html[end_idx + len(GALLERY_END):]

    # Update translations
    en_entries, es_entries = build_translations(radios)
    html = update_translations(html, en_entries, es_entries)

    INDEX_HTML.write_text(html)
    print(f"Built gallery with {len(radios)} radio(s):")
    for r in radios:
        st = r.get("status", "sale")
        label = {"sold": "SOLD", "collection": "COLLECTION"}.get(st, format_price(r.get("price", 0)))
        print(f"  {r['year']} {r['model']} — {label}")


if __name__ == "__main__":
    main()
