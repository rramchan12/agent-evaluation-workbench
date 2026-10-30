# scripts/

Standalone, manual helper scripts -- not part of `pytest`/CI.

- `capture_screenshots.py`: drives the Streamlit GUI with Playwright
  (headless Chromium) to (re)generate the PNGs used in the top-level
  README's "GUI" section (`docs/screenshots/*.png`). Requires
  `pip install playwright && playwright install chromium`. Re-run by hand
  whenever the GUI's look changes enough to make the screenshots stale.
