# MKDSrust branding report

## Files changed

- `assets/icon.png`: exact, byte-for-byte copy of the owner's `C:\Users\cam\dev\logos\final\icon_236.png`.
- `assets/favicon.png`: 32 × 32 PNG favicon derived from the final wheel.
- `assets/logo.svg`: final wheel embedded in the SVG, replacing option 3's old icon, with the Apex Trace wordmark retained. Self-contained for README and site use.
- `build.py`: shared favicon link and accessible header logo on every generated page; full logo in the home hero.
- `assets/theme.css`: rust orange, teal, charcoal and yellow accents; responsive logo sizing; light/dark surfaces, text, links, controls, table states, badges and focus colors.
- `assets/ATTRIBUTION.md`: supplied branding sources and distinction from unused legacy game graphics.
- `README.md`: logo at the top and updated asset scope description.
- `BRAND_REPORT.md`: this report.
- `_site/*.html` and `_site/assets/`: refreshed local preview output (gitignored).

## Verification and build limitation

- Visually inspected the supplied wheel and an Inkscape-rendered preview of the combined logo. The final wheel and Apex Trace wordmark render together without clipping.
- Confirmed `assets/icon.png` matches the owner's source bytes exactly.
- Attempted `build.py` using the installed Blender CPython 3.11.11, because `python` is absent from PATH. It stopped at `ModuleNotFoundError: No module named 'markdown_it'`.
- Attempted to install the pinned `markdown-it-py==4.2.0` into the ignored local `.deps` directory. Sandbox network restrictions blocked PyPI. Other discovered local copies were unreadable under sandbox permissions. The Python unittest suite is blocked by the same import.
- To provide reviewable output, evaluated the actual `build.py` shared `frame` function with its standard-library dependencies, refreshed all 47 existing output pages using their existing rendered bodies, inserted the home hero logo, and copied current assets. This refresh preserves rendered content and sidebar selection; it is **not a full Markdown rebuild**.
- Verified every one of the 47 output pages references `assets/favicon.png` and the header `assets/logo.svg`; verified the home hero logo and all referenced local assets exist.
- `node tests/explorer.cjs`: passed all five sorts in both directions, 200-row batches, filters, exhaustion and stable details against 11,175 records.

A full build remains to be run in an environment with the pinned dependency available:

```powershell
python -m pip install -r requirements.txt
python build.py
python -m unittest discover -s tests -v
node tests/explorer.cjs
```

No commit or push was made. Original logo source files were not changed.
