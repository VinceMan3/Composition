# Tools

Everything here is for building and checking the app. None of it ships; the
app itself still needs no build step.

| File | What it does |
| --- | --- |
| `test/run.py` | The full set of checks (305 at last count), run in a real browser |
| `test/common.py` | Shared setup for the checks: fonts, error capture, screenshots |
| `build-preview.py` | Packs the app into one page for a Claude preview, in `tools/preview/` |
| `serve.sh` | Starts the two local servers the checks use |
| `art/ink.py` | Lifts pen ink off a photo of ruled paper (used for the hand sketches) |
| `art/badges.py` | Draws the earned stickers |
| `art/textures.py` | Makes the paper and cover textures |
| `art/icon.py` | Draws the home-screen icon |

## Setup, once

    cd tools && npm install && cd ..
    pip install playwright numpy pillow --break-system-packages   # if missing

## Running the checks

From the repository root:

    python3 tools/build-preview.py
    sh tools/serve.sh
    python3 tools/test/run.py                                          # the app, port 8770
    python3 tools/test/run.py http://127.0.0.1:8771/_local.html /tmp/p  # the preview, port 8771

Every line prints PASS or FAIL. Screenshots land in `tools/test/shots/`
(not kept in git). Browser contexts block the offline worker except in the
offline check, which is skipped for the preview.
