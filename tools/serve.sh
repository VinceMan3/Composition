#!/bin/sh
# Starts the two local servers the checks use, if they are not already up:
# the app on 8770 and the single-file preview (tools/preview/) on 8771.
# Run from the repository root: sh tools/serve.sh
ROOT=$(cd "$(dirname "$0")/.." && pwd)
curl -s -o /dev/null http://127.0.0.1:8770/index.html || (cd "$ROOT" && nohup python3 -m http.server 8770 --bind 127.0.0.1 >/dev/null 2>&1 &)
curl -s -o /dev/null http://127.0.0.1:8771/_local.html || (cd "$ROOT/tools/preview" && nohup python3 -m http.server 8771 --bind 127.0.0.1 >/dev/null 2>&1 &)
sleep 1
