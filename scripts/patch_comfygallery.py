#!/usr/bin/env python3
"""Teach ComfyGallery's browser button how to open its Runpod HTTP port."""

from __future__ import annotations

import argparse
from pathlib import Path


MARKER = "Runpod exposes Gallery on the pod's 8190 HTTP proxy"
ANCHOR = """async function launchGallery() {
  if (launchPending) return;
"""
REPLACEMENT = f"""async function launchGallery() {{
  if (launchPending) return;

  // {MARKER}. Keep upstream behavior everywhere else.
  const runpodMatch = window.location.hostname.match(/^(.*)-8188\\.proxy\\.runpod\\.net$/i);
  if (runpodMatch) {{
    const galleryUrl = `${{window.location.protocol}}//${{runpodMatch[1]}}-8190.proxy.runpod.net/`;
    const browserTab = window.open("about:blank", "_blank");
    if (!browserTab) {{
      showToast("error", "ComfyGallery", "Allow pop-ups for ComfyUI, then click Gallery again.");
      return;
    }}
    registerGalleryOrigin(galleryUrl);
    browserTab.location.replace(connectBrowserGallery(browserTab, galleryUrl));
    return;
  }}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("javascript", type=Path)
    args = parser.parse_args()

    source = args.javascript.read_text(encoding="utf-8")
    if MARKER in source:
        return 0
    if source.count(ANCHOR) != 1:
        raise RuntimeError(
            "ComfyGallery's launch function changed upstream; update the Runpod patch before building."
        )
    args.javascript.write_text(source.replace(ANCHOR, REPLACEMENT), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
